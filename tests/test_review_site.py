"""The preview builder must not overwrite user files or reuse stale assets."""

from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewSiteGuards(unittest.TestCase):
    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="hdmi2c-site-test-") as directory:
            base = Path(directory)
            tool = base / "tool"
            (tool / "InteractiveHtmlBom").mkdir(parents=True)
            (tool / "InteractiveHtmlBom/generate_interactive_bom.py").touch()
            (tool / "LICENSE").touch()
            output = base / "out"
            output.mkdir()
            sentinel = output / "user-file.step"
            sentinel.write_text("must not delete or publish me")
            result = subprocess.run(["bash", str(ROOT / "scripts/build_review_site.sh"),
                                     str(tool), str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("must be a new directory", result.stderr)
            self.assertEqual(sentinel.read_text(), "must not delete or publish me")
            self.assertEqual(list(output.iterdir()), [sentinel])

    def test_missing_tool_does_not_create_output(self):
        with tempfile.TemporaryDirectory(prefix="hdmi2c-site-test-") as directory:
            base = Path(directory)
            output = base / "out"
            result = subprocess.run(["bash", str(ROOT / "scripts/build_review_site.sh"),
                                     str(base / "missing"), str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Expected an InteractiveHtmlBom checkout", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
