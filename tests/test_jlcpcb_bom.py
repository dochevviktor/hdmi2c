"""Protect purchasing identities and JLCPCB's ambiguous duplicate CSV columns."""

import csv
import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_jlcpcb_bom import PARTS, audit, draft_rows, expand_refs, read_matches


class JlcpcbBomChecks(unittest.TestCase):
    def fixture(self):
        # Synthetic snapshot: future edits to the user's real CSV must not turn
        # this intentional wrong-part test into a requirement to retain bad data.
        rows = [["Designator", "Comment", "Footprint", "JLCPCB Part #", "Part # ",
                 "Footprint", "Description", "JLCPCB Part #"]]
        for refs in ("U3", "R24,R25", "SW2,SW3", "U4", "R26,R27", "C1-C3", "J7"):
            ref = expand_refs(refs)[0]
            mpn, code = PARTS[ref]
            if ref == "J7":
                mpn, code = "PI3HDMI1310-AZLEX", "C516617"
            rows.append([refs, "value", "reviewed-footprint", "", mpn,
                         "reviewed-footprint", "Description with\na newline", code])
        return rows

    def parse(self, rows):
        stream = io.StringIO()
        csv.writer(stream).writerows(rows)
        stream.seek(0)
        return read_matches(stream)

    def test_reference_ranges(self):
        self.assertEqual(expand_refs("C1-C3,R24,R25"), ["C1", "C2", "C3", "R24", "R25"])
        for value in ("C3-C1", "C1-R3", "C1,C1"):
            with self.assertRaises(ValueError):
                expand_refs(value)

    def test_selected_column_and_multiline_description(self):
        matches = self.parse(self.fixture())
        self.assertEqual(matches["U3"]["JLCPCB Part #"], "C27675191")
        self.assertEqual(matches["C3"]["JLCPCB Part #"], "C14663")
        self.assertEqual(len(matches), 12)

    def test_conflicting_duplicate_column(self):
        rows = self.fixture()
        rows[1][3] = "C999999"
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate column"):
            self.parse(rows)

    def test_missing_or_duplicate_component(self):
        rows = self.fixture()
        with self.assertRaisesRegex(ValueError, "exactly the 12"):
            self.parse(rows[:-1])
        with self.assertRaisesRegex(ValueError, "Duplicate designator"):
            self.parse(rows + [rows[1]])

    def test_wrong_hdmi_ic_is_rejected(self):
        matches = self.parse(self.fixture())
        design = {ref: {"mpn": mpn, "code": code, "footprint": matches[ref]["Footprint"]}
                  for ref, (mpn, code) in PARTS.items()}
        results = audit(matches, design)
        self.assertEqual([r["reference"] for r in results if r["status"] != "MATCHED_REVIEWED"], ["J7"])
        self.assertEqual(next(r for r in results if r["reference"] == "J7")["status"], "REJECTED")

    def test_draft_keeps_connector_without_wrong_code(self):
        matches = self.parse(self.fixture())
        design = {ref: {"mpn": mpn, "code": code, "footprint": matches[ref]["Footprint"]}
                  for ref, (mpn, code) in PARTS.items()}
        rows = draft_rows(design)
        self.assertEqual(sum(r["Quantity"] for r in rows), 12)
        connector = next(r for r in rows if r["Designator"] == "J7")
        self.assertEqual(connector["Comment"], "685119134923")
        self.assertEqual(connector["LCSC Part #"], "C2930961")
        self.assertNotIn("C516617", str(rows))

    def test_correct_wurth_connector_is_accepted(self):
        matches = self.parse(self.fixture())
        matches["J7"]["Part #"], matches["J7"]["JLCPCB Part #"] = PARTS["J7"]
        design = {ref: {"mpn": mpn, "code": code, "footprint": matches[ref]["Footprint"]}
                  for ref, (mpn, code) in PARTS.items()}
        self.assertTrue(all(r["status"] == "MATCHED_REVIEWED" for r in audit(matches, design)))

    def test_correct_connector_code_with_wrong_footprint_is_rejected(self):
        matches = self.parse(self.fixture())
        matches["J7"]["Part #"], matches["J7"]["JLCPCB Part #"] = PARTS["J7"]
        design = {ref: {"mpn": mpn, "code": code, "footprint": matches[ref]["Footprint"]}
                  for ref, (mpn, code) in PARTS.items()}
        matches["J7"]["Footprint"] = "unreviewed-footprint"
        connector = next(r for r in audit(matches, design) if r["reference"] == "J7")
        self.assertEqual(connector["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
