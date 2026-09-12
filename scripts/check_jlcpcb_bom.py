#!/usr/bin/env python3
"""Review JLCPCB matching CSV against pinned, reviewed rev2 purchasing fields.

Never rewrites the user's matching CSV. Draft BOMs come from the schematic, not
the auto-matched catalog row. A match does not establish stock or assembly approval.
"""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


# Reviewed on 2026-09-12; see docs/jlcpcb.md. J7 deliberately has no approved code.
PARTS = {
    **dict.fromkeys(("C1", "C2", "C3"), ("CC0603KRX7R9BB104", "C14663")),
    **dict.fromkeys(("R24", "R25"), ("FRH0603B1003TS", "C51048211")),
    **dict.fromkeys(("R26", "R27"), ("SC0603F1002F2BNRH", "C3152123")),
    **dict.fromkeys(("SW2", "SW3"), ("B3U-1000P", "C231329")),
    "U3": ("113991254", "C27675191"),
    "U4": ("TPD12S016PWR", "C201665"),
    "J7": ("685119134923", ""),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expand_refs(value):
    refs = []
    for token in value.replace(" ", "").split(","):
        match = re.fullmatch(r"([A-Z]+)(\d+)(?:-([A-Z]+)?(\d+))?", token)
        require(match is not None, f"Invalid designator/range: {token}")
        prefix, first, end_prefix, last = match.groups()
        require(end_prefix in (None, prefix), f"Mixed reference range: {token}")
        start, end = int(first), int(last or first)
        require(start <= end < start + 1000, f"Invalid reference range: {token}")
        refs.extend(f"{prefix}{number}" for number in range(start, end + 1))
    require(len(set(refs)) == len(refs), f"Repeated designator: {value}")
    return refs


def read_matches(stream):
    reader = csv.reader(stream)
    headers = [h.strip() for h in next(reader)]
    require({"Designator", "Part #", "JLCPCB Part #", "Footprint"} <= set(headers),
            "Expected the JLCPCB part-matching report headers")
    result = {}
    for row in reader:
        if not row:
            continue
        require(len(row) == len(headers), "Malformed CSV row")
        columns = defaultdict(set)
        for name, value in zip(headers, row):
            if value.strip():
                columns[name].add(value.strip())
        # JLCPCB repeats Part # and Footprint columns. Do not silently take a
        # blank first column or an inconsistent last value as DictReader would.
        for name, values in columns.items():
            require(len(values) == 1, f"Conflicting duplicate column: {name}")
        fields = {name: next(iter(values)) for name, values in columns.items()}
        for ref in expand_refs(fields.get("Designator", "")):
            require(ref not in result, f"Duplicate designator: {ref}")
            result[ref] = fields
    require(set(result) == set(PARTS), "Matching CSV must cover exactly the 12 fitted components")
    return result


def read_design(path):
    result = {}
    for comp in ET.parse(path).findall("./components/comp"):
        ref = comp.get("ref")
        if ref not in PARTS:
            continue
        fields = {f.get("name"): f.text or "" for f in comp.findall("./fields/field")}
        actual = (fields.get("MPN", ""), fields.get("LCSC Part #", ""))
        require(actual == PARTS[ref], f"Unreviewed schematic purchasing fields: {ref}: {actual}")
        result[ref] = {"mpn": actual[0], "code": actual[1],
                       "footprint": comp.findtext("footprint", "")}
    require(set(result) == set(PARTS), "Incomplete schematic component data")
    return result


def audit(matches, design):
    results = []
    for ref in sorted(PARTS):
        selected = matches[ref]
        expected = design[ref]
        mpn, code = selected.get("Part #", ""), selected.get("JLCPCB Part #", "")
        same = ((mpn, code) == (expected["mpn"], expected["code"]) and
                selected["Footprint"] == expected["footprint"])
        status = "MATCHED_REVIEWED" if same and expected["code"] else "NEEDS_REVIEW"
        note = "Part identity reviewed; inventory, placement and assembly acceptance still require confirmation."
        if ref == "J7":
            status = "UNRESOLVED" if mpn == expected["mpn"] and not code else "REJECTED"
            note = ("J7 requires Wurth 685119134923. C516617 / PI3HDMI1310-AZLEX is a "
                    "TQFN HDMI switch IC, not a connector. No replacement code is approved.")
        results.append({"reference": ref, "status": status, "selected_mpn": mpn,
                        "selected_code": code, "schematic_mpn": expected["mpn"],
                        "approved_code": expected["code"], "note": note})
    return results


def draft_rows(design):
    groups = defaultdict(list)
    for ref, part in sorted(design.items()):
        groups[(part["mpn"], part["footprint"], part["code"])].append(ref)
    return [{"Comment": mpn, "Designator": ",".join(refs), "Footprint": footprint,
             "LCSC Part #": code, "Quantity": len(refs)}
            for (mpn, footprint, code), refs in sorted(groups.items())]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matching_csv", type=Path)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--draft-bom", type=Path)
    parser.add_argument("--allow-unresolved-j7", action="store_true",
                        help="Allow only the documented J7 blocker for draft/CAD exports")
    args = parser.parse_args()
    with args.matching_csv.open(newline="", encoding="utf-8-sig") as stream:
        matches = read_matches(stream)
    design = read_design(args.netlist)
    results = audit(matches, design)
    pending = [r["reference"] for r in results if r["status"] != "MATCHED_REVIEWED"]
    report = {"status": "BLOCKED — not an assembly release" if pending else "BOM identities matched only",
              "ready_for_order": False, "matching_csv_sha256": sha256(args.matching_csv),
              "netlist_sha256": sha256(args.netlist), "unresolved_references": pending,
              "parts": results,
              "remaining": ["Resolve J7 sourcing without an unreviewed footprint substitution.",
                            "Confirm XIAO module reflow/handling and HDMI shell-tab soldering with JLCPCB.",
                            "Confirm assembly service, tooling/panel needs and corrected CPL origins/rotations.",
                            "Recheck availability, quote and physical validation; no order has been placed."]}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    permitted_draft = pending == ["J7"] and args.allow_unresolved_j7
    if pending and not permitted_draft:
        print(f"BLOCKED: JLCPCB BOM review required for {', '.join(pending)}", file=sys.stderr)
        return 1
    if args.draft_bom:
        rows = draft_rows(design)
        with args.draft_bom.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print("DRAFT ONLY: 11 component identities matched; J7 sourcing and assembly approval remain unresolved.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, StopIteration) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
