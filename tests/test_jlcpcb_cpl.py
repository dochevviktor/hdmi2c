"""Protect JLCPCB CPL column mapping without claiming machine-placement approval."""

import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from export_jlcpcb_cpl import CPL_COLUMNS, cpl_rows


class JlcpcbCplChecks(unittest.TestCase):
    positions = "Ref,Val,Package,PosX,PosY,Rot,Side\nC1,100nF,C_0603,1.234567,-2.345678,270.000000,top\n"
    bom = "Comment,Designator,Footprint,LCSC Part #,Quantity\n100nF,C1,C_0603,C14663,1\n"

    def convert(self, positions=None, bom=None):
        return cpl_rows(io.StringIO(self.positions if positions is None else positions),
                        io.StringIO(self.bom if bom is None else bom))

    def test_exact_example_schema_and_precision(self):
        rows = self.convert()
        self.assertEqual(tuple(rows[0]), ("Designator", "Mid X", "Mid Y", "Layer", "Rotation"))
        self.assertEqual(rows, [{"Designator": "C1", "Mid X": "1.234567mm",
                                 "Mid Y": "-2.345678mm", "Layer": "Top", "Rotation": "270"}])

    def test_bottom_side_is_not_mirrored(self):
        row = self.convert(self.positions.replace(",top", ",bottom"))[0]
        self.assertEqual((row["Mid X"], row["Mid Y"], row["Rotation"], row["Layer"]),
                         ("1.234567mm", "-2.345678mm", "270", "Bottom"))

    def test_rotation_normalization_preserves_direction(self):
        for original, expected in (("-90", "270"), ("450", "90"), ("360", "0"),
                                   ("-0.000", "0"), ("12.500000", "12.5")):
            with self.subTest(rotation=original):
                row = self.convert(self.positions.replace("270.000000", original))[0]
                self.assertEqual(row["Rotation"], expected)

    def test_invalid_coordinates_rotation_or_side_are_rejected(self):
        for old, bad in (("1.234567", "NaN"), ("-2.345678", "Infinity"),
                         ("270.000000", "-Infinity"), ("1.234567", "1mm"),
                         ("270.000000", ""), (",top", ",unknown")):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                self.convert(self.positions.replace(old, bad))

    def test_wrong_schema_and_malformed_rows_are_rejected(self):
        for value in ("", self.positions.splitlines()[0] + "\n", self.bom,
                      self.positions.replace("PosY", "PosX"),
                      self.positions.replace(",top", ""), self.positions.replace(",top", ",top,extra")):
            with self.subTest(positions=value), self.assertRaises(ValueError):
                self.convert(value)

    def test_grouped_bom_and_reference_mismatches(self):
        grouped = self.bom.replace("C1,C_0603", '"C1,C2",C_0603').replace("C14663,1", "C14663,2")
        second = self.positions.splitlines()[1].replace("C1,", "C2,") + "\n"
        self.assertEqual(len(self.convert(self.positions + second, grouped)), 2)
        for positions, bom in ((self.positions, grouped), (self.positions + second, self.bom),
                               (self.positions + second.replace("C2,", "C1,"), self.bom),
                               (self.positions.replace("C1,", "C1-C2,"), grouped),
                               (self.positions, self.bom + self.bom.splitlines()[1] + "\n"),
                               (self.positions, self.bom.replace("C14663,1", "C14663,2"))):
            with self.subTest(positions=positions, bom=bom), self.assertRaises(ValueError):
                self.convert(positions, bom)

    def test_current_board_includes_hdmi_and_excludes_etched_test_pads(self):
        with (ROOT / "hardware/rev2/positions-front.csv").open(newline="") as positions, \
                (ROOT / "hardware/rev2/bom-jlcpcb-draft.csv").open(newline="") as bom:
            raw = list(csv.DictReader(positions))
            positions.seek(0)
            rows = cpl_rows(positions, bom)
        refs = {r["Designator"] for r in rows}
        self.assertEqual(refs, {"C1", "C2", "C3", "J7", "R24", "R25", "R26", "R27", "SW2", "SW3", "U3", "U4"})
        for source, row in zip(raw, rows):
            self.assertEqual(Decimal(source["PosX"]), Decimal(row["Mid X"].removesuffix("mm")))
            self.assertEqual(Decimal(source["PosY"]), Decimal(row["Mid Y"].removesuffix("mm")))
            self.assertEqual(row["Layer"], "Top")

    def run_export(self, positions, bom, output, report):
        return subprocess.run([sys.executable, str(ROOT / "scripts/export_jlcpcb_cpl.py"),
                               str(positions), str(bom), "--output", str(output), "--report", str(report)],
                              capture_output=True, text=True)

    def test_cli_writes_draft_report_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory(prefix="hdmi2c-cpl-test-") as directory:
            base = Path(directory)
            positions = ROOT / "hardware/rev2/positions-front.csv"
            bom = ROOT / "hardware/rev2/bom-jlcpcb-draft.csv"
            before = [path.read_bytes() for path in (positions, bom)]
            output, report = base / "cpl.csv", base / "checks/cpl.json"
            result = self.run_export(positions, bom, output, report)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text().splitlines()[0], ",".join(CPL_COLUMNS))
            audit = json.loads(report.read_text())
            self.assertEqual(audit["component_count"], 12)
            self.assertTrue(audit["bom_reference_match"])
            self.assertFalse(audit["ready_for_order"])
            self.assertEqual(audit["known_non_centroid_origins"], ["J7", "U3"])
            self.assertEqual(len(audit["placement_review_required"]), 12)
            self.assertEqual(audit["cpl_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(before, [path.read_bytes() for path in (positions, bom)])

    def test_invalid_input_does_not_overwrite_previous_output(self):
        with tempfile.TemporaryDirectory(prefix="hdmi2c-cpl-test-") as directory:
            base = Path(directory)
            positions, bom, output, report = (base / name for name in ("pos.csv", "bom.csv", "cpl.csv", "cpl.json"))
            positions.write_text(self.positions.replace("C1,", "J7,"))
            bom.write_text(self.bom)
            output.write_text("previous output")
            report.write_text("previous report")
            result = self.run_export(positions, bom, output, report)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reference mismatch", result.stderr)
            self.assertEqual(output.read_text(), "previous output")
            self.assertEqual(report.read_text(), "previous report")

    def test_input_output_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="hdmi2c-cpl-test-") as directory:
            base = Path(directory)
            positions, bom = base / "pos.csv", base / "bom.csv"
            positions.write_text(self.positions)
            bom.write_text(self.bom)
            alias = base / "alias.csv"
            alias.symlink_to(bom)
            hardlink = base / "hardlink.csv"
            hardlink.hardlink_to(positions)
            for output, report in ((bom, base / "report.json"), (base / "cpl.csv", positions),
                                   (base / "same", base / "same"),
                                   (alias, base / "report.json"), (hardlink, base / "report.json")):
                with self.subTest(output=output, report=report):
                    result = self.run_export(positions, bom, output, report)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("distinct files", result.stderr)
                    self.assertEqual(positions.read_text(), self.positions)
                    self.assertEqual(bom.read_text(), self.bom)


if __name__ == "__main__":
    unittest.main()
