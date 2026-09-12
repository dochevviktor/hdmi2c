"""Fault-injection tests for the rev2 design-contract checker (requires KiCad)."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def make_fixture(case, output):
    # Isolate pcbnew's native board lifetime per process (KiCad 10 / Python 3.14).
    import pcbnew as k
    board = k.LoadBoard(str(ROOT / "hdmi2c.kicad_pcb"))
    feet = {f.GetReference(): f for f in board.GetFootprints()}

    def pad(ref, number):
        return next(p for p in feet[ref].Pads() if p.GetNumber() == str(number))

    if case == "test_swapped_sda_scl":
        sda, scl = pad("U3", 5), pad("U3", 6)
        sda_net, scl_net = sda.GetNet(), scl.GetNet()
        sda.SetNet(scl_net)
        scl.SetNet(sda_net)
    elif case == "test_direct_five_volts_to_gpio":
        pad("U3", 5).SetNet(pad("J7", 18).GetNet())
    elif case == "test_wrong_castellation_land":
        land = pad("U3", 1)
        position = land.GetPosition()
        position.x += k.FromMM(.1)
        land.SetPosition(position)
    elif case in ("test_missing_antenna_keepout", "test_weakened_antenna_keepout"):
        zone = next(z for z in board.Zones() if z.GetZoneName().startswith("XIAO antenna:"))
        if case == "test_missing_antenna_keepout":
            board.Remove(zone)
        else:
            zone.SetDoNotAllowTracks(False)
    elif case == "test_missing_xiao_model":
        feet["U3"].Models().clear()
    elif case == "test_wrong_xiao_model_rotation":
        feet["U3"].Models()[0].m_Rotation.z = 90
    elif case == "test_wrong_xiao_model_height":
        feet["U3"].Models()[0].m_Offset.z = 0
    elif case != "test_reviewed_design":
        raise ValueError(f"Unknown fixture: {case}")
    k.SaveBoard(output, board)


class Rev2Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="hdmi2c-check-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.netlist = Path(cls.temp.name) / "netlist.xml"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
                        "-o", str(cls.netlist), str(ROOT / "hdmi2c.kicad_sch")], check=True,
                       capture_output=True, text=True)

    def check_result(self, expected_error=None):
        board_path = Path(self.temp.name) / "fixture.kicad_pcb"
        subprocess.run([sys.executable, __file__, "--make-fixture", self._testMethodName,
                        str(board_path)], check=True, capture_output=True, text=True)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/check_rev2.py"),
                                 str(board_path), str(self.netlist)], capture_output=True, text=True)
        if expected_error is None:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(expected_error, result.stderr)

    def test_reviewed_design(self):
        self.check_result()

    def test_swapped_sda_scl(self):
        self.check_result("Unexpected connections on I2C_SDA")

    def test_direct_five_volts_to_gpio(self):
        self.check_result("Unexpected connections on I2C_SDA")

    def test_wrong_castellation_land(self):
        self.check_result("XIAO pad geometry/numbering changed")

    def test_missing_antenna_keepout(self):
        self.check_result("Missing safety keepout")

    def test_weakened_antenna_keepout(self):
        self.check_result("Weakened keepout")

    def test_missing_xiao_model(self):
        self.check_result("XIAO must have exactly one detailed 3D model")

    def test_wrong_xiao_model_rotation(self):
        self.check_result("XIAO 3D model m_Rotation changed")

    def test_wrong_xiao_model_height(self):
        self.check_result("XIAO 3D model m_Offset changed")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--make-fixture":
        make_fixture(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
