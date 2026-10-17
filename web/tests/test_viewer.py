"""Runs web/tests/viewer_test.mjs (the WebGL viewer's cache, invalidation and error reasons) under Node, if installed."""
import pathlib
import shutil
import subprocess
import unittest

NODE = shutil.which("node")
HERE = pathlib.Path(__file__).resolve().parent


@unittest.skipUnless(NODE, "node is not installed")
class ViewerModuleTest(unittest.TestCase):
    def testViewerChecksPass(self):
        r = subprocess.run([NODE, str(HERE / "viewer_test.mjs")], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("viewer checks passed", r.stdout)


if __name__ == "__main__":
    unittest.main()
