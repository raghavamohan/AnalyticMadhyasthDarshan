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
GUARD = SCRIPTS / "vendor/extract-zip-guard/index.js"
# Same Unix mode mask as vendor/extract-zip-guard/index.js.
IFMT = 61440
IFLNK = 40960
SYMLINK_MODE = 0o120777


def _symlink_zip(root: Path) -> tuple[Path, Path]:
    archive = root / "evil.zip"
    dest = root / "out"
    dest.mkdir()
    with zipfile.ZipFile(archive, "w") as zipper:
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (SYMLINK_MODE & 0xFFFF) << 16
        zipper.writestr(info, "/tmp/evil")
    return archive, dest


class ExtractZipGuardTests(unittest.TestCase):
    def test_package_override_points_at_the_local_guard(self):
        package = json.loads((SCRIPTS / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((SCRIPTS / "package-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(package["dependencies"]["extract-zip"], "file:vendor/extract-zip-guard")
        self.assertEqual(package["overrides"]["extract-zip"], "$extract-zip")
        linked = lock["packages"]["node_modules/extract-zip"]
        self.assertEqual(linked["resolved"], "vendor/extract-zip-guard")
        self.assertTrue(linked.get("link"))
        self.assertEqual(lock["packages"]["vendor/extract-zip-guard"]["name"], "extract-zip")
        source = GUARD.read_text(encoding="utf-8")
        self.assertIn("const IFLNK = 40960", source)
        self.assertIn("const symlink = (mode & IFMT) === IFLNK", source)
        self.assertIn('Refusing to extract symlink', source)
        self.assertNotIn("fs.symlink", source)
        self.assertLess(
            source.index("if (symlink)"),
            source.index("pipeline(readStream, createWriteStream"),
        )

    def test_crafted_zip_sets_the_unix_symlink_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            archive, _dest = _symlink_zip(Path(directory))
            with zipfile.ZipFile(archive) as zipper:
                mode = (zipper.getinfo("link").external_attr >> 16) & 0xFFFF
            self.assertEqual(mode & IFMT, IFLNK)

    def test_symlink_zip_is_rejected(self):
        if not (SCRIPTS / "node_modules" / "yauzl").exists():
            self.skipTest("Scripts/node_modules is not installed in the checks job")
        with tempfile.TemporaryDirectory() as directory:
            archive, dest = _symlink_zip(Path(directory))
            script = (
                "const extract=require('./vendor/extract-zip-guard');"
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
