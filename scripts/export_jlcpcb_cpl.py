#!/usr/bin/env python3
"""Format a KiCad millimetre placement CSV as a JLCPCB CPL draft.

This is a column/unit conversion, not a machine-placement calibration. Keep the
source XY coordinates; never shift or mirror them independently of the Gerbers.
In rev2, U3 and J7 have non-centroid origins that still need assembler review.
"""

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys

from check_jlcpcb_bom import expand_refs, require


CPL_COLUMNS = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")
POSITION_COLUMNS = ("Ref", "PosX", "PosY", "Rot", "Side")


def read_table(stream, required, label):
    reader = csv.reader(stream, strict=True)
    headers = [value.strip() for value in next(reader, [])]
    require(set(required) <= set(headers), f"Expected {label} columns: {', '.join(required)}")
    require(len(headers) == len(set(headers)), f"Duplicate {label} column")
    rows = []
    for values in reader:
        if not values:
            continue
        require(len(values) == len(headers), f"Malformed {label} CSV row")
        rows.append(dict(zip(headers, (value.strip() for value in values))))
    require(rows, f"Empty {label} data")
    return rows


def number(value, ref, column):
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"Invalid {column} for {ref}: {value!r}") from error
    require(result.is_finite(), f"Non-finite {column} for {ref}: {value!r}")
    return result


def cpl_rows(positions, bom):
    expected = set()
    for row in read_table(bom, ("Designator", "Quantity"), "clean BOM"):
        refs = expand_refs(row["Designator"])
        require(row["Quantity"].isdigit() and int(row["Quantity"]) == len(refs),
                f"BOM quantity does not match designators: {row['Designator']}")
        require(not expected.intersection(refs), f"Duplicate BOM designator: {row['Designator']}")
        expected.update(refs)

    rows, seen = [], set()
    for row in read_table(positions, POSITION_COLUMNS, "KiCad placement"):
        ref = row["Ref"]
        require(expand_refs(ref) == [ref], f"Expected one placement designator: {ref}")
        require(ref not in seen, f"Duplicate placement designator: {ref}")
        seen.add(ref)
        side = row["Side"].lower()
        require(side in ("top", "bottom"), f"Invalid placement side for {ref}: {row['Side']!r}")
        x, y = (number(row[column], ref, column) for column in ("PosX", "PosY"))
        rotation = number(row["Rot"], ref, "Rot") % 360
        if rotation < 0:
            rotation += 360
        angle = format(rotation, "f")
        if "." in angle:
            angle = angle.rstrip("0").rstrip(".")
        rows.append({"Designator": ref, "Mid X": f"{x:f}mm", "Mid Y": f"{y:f}mm",
                     "Layer": side.title(), "Rotation": "0" if rotation == 0 else angle})
    require(seen == expected,
            f"CPL/BOM reference mismatch: missing {sorted(expected - seen)}, extra {sorted(seen - expected)}")
    return rows


def distinct_paths(paths):
    for index, path in enumerate(paths):
        for earlier in paths[:index]:
            same = path.resolve() == earlier.resolve()
            if path.exists() and earlier.exists():
                same = same or path.samefile(earlier)
            require(not same, f"Inputs and outputs must be distinct files: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positions", type=Path, help="KiCad CSV exported with --units mm")
    parser.add_argument("bom", type=Path, help="clean BOM for the same revision, with Quantity")
    parser.add_argument("--output", type=Path, required=True, help="JLCPCB-format draft CPL")
    parser.add_argument("--report", type=Path, required=True, help="format audit and placement caveats")
    args = parser.parse_args()
    try:
        distinct_paths([args.positions, args.bom, args.output, args.report])
        with args.positions.open(encoding="utf-8-sig", newline="") as positions, \
                args.bom.open(encoding="utf-8-sig", newline="") as bom:
            rows = cpl_rows(positions, bom)
        report = {
            "status": "FORMAT_ONLY_REVIEW_REQUIRED",
            "ready_for_order": False,
            "columns": CPL_COLUMNS,
            "units": "mm",
            "component_count": len(rows),
            "bom_reference_match": True,
            "coordinate_transform": "None; source XY retained, including signs. Input must be millimetres.",
            "rotation_transform": "Normalized to [0, 360) degrees; no component-specific corrections.",
            "known_non_centroid_origins": sorted({"U3", "J7"} & {r["Designator"] for r in rows}),
            "placement_review_required": [r["Designator"] for r in rows],
            "note": "Review offsets, pin 1, USB/HDMI direction and all rotations in JLCPCB's placement preview. "
                    "Correct column formatting does not establish correct machine placement or assembly approval.",
            "input_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (args.positions, args.bom)},
        }
        # Validate everything before opening outputs; input files are never rewritten.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=CPL_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        report["cpl_sha256"] = hashlib.sha256(args.output.read_bytes()).hexdigest()
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (ValueError, InvalidOperation, csv.Error, OSError) as error:
        print(f"CPL export failed: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {len(rows)}-component JLCPCB-format draft: {args.output}")
    print("Placement offsets/rotations are NOT approved; see the accompanying report.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
