"""Guard the local extract-zip override against symlink extraction."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from _common import BASE


SCRIPTS = BASE / "Scripts"


class ExtractZipGuardTests(unittest.TestCase):
    def test_package_override_points_at_the_local_guard(self):
        package = json.loads((SCRIPTS / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["dependencies"]["extract-zip"], "file:vendor/extract-zip-guard")
        self.assertEqual(package["overrides"]["extract-zip"], "$extract-zip")
        source = (SCRIPTS / "vendor/extract-zip-guard/index.js").read_text(encoding="utf-8")
        self.assertIn('Refusing to extract symlink', source)
        self.assertNotIn('fs.symlink', source)

    def test_symlink_zip_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "evil.zip"
            dest = root / "out"
            dest.mkdir()
            with zipfile.ZipFile(archive, "w") as zipper:
                info = zipfile.ZipInfo("link")
                info.create_system = 3
                info.external_attr = (0o120777 & 0xFFFF) << 16
                zipper.writestr(info, "/tmp/evil")
            script = (
                "const extract=require('extract-zip');"
                "extract(" + json.dumps(str(archive)) + ",{dir:" + json.dumps(str(dest)) + "})"
                ".then(()=>process.exit(2))"
                ".catch(err=>{if(!/symlink/i.test(String(err.message))) {console.error(err); process.exit(3);}});"
            )
            result = subprocess.run(
                ["node", "-e", script],
                cwd=str(SCRIPTS),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((dest / "link").exists())


if __name__ == "__main__":
    unittest.main()
