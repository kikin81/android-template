"""Self-test for scripts/rename.py.

Runs against a fresh `android create empty-activity` output in a tmpdir and
asserts the rename pipeline produces the expected state. Use:

    python3 -m unittest scripts/test_rename.py

Set RUN_FULL_BUILD=1 to also run `./gradlew :app:assembleDebug` after the
rename; CI always sets this.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RENAME_SCRIPT = REPO_ROOT / "scripts" / "rename.py"


def _scaffold(dest: Path) -> None:
    """Generate a fresh `android create` project at `dest`."""
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["android", "create", "empty-activity", "--name=My App", f"--output={dest}"],
        check=True,
    )
    shutil.copy2(RENAME_SCRIPT, dest / "rename.py")


def _run_rename(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(project / "rename.py"), *args],
        cwd=project,
        capture_output=True,
        text=True,
    )


class RenameCliTest(unittest.TestCase):
    def test_rejects_invalid_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            _scaffold(project)
            result = _run_rename(
                project,
                "--package", "Com.Bad.Case",
                "--app-name", "Acme Widget",
                "--app-name-pascal", "AcmeWidget",
                "--app-name-lower", "acmewidget",
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("--package", result.stderr)

    def test_preflight_fails_when_no_template_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            shutil.copy2(RENAME_SCRIPT, project / "rename.py")
            result = _run_rename(
                project,
                "--package", "com.acme.widget",
                "--app-name", "Acme Widget",
                "--app-name-pascal", "AcmeWidget",
                "--app-name-lower", "acmewidget",
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("com.example.myapp", result.stderr)


class RenameDirectoriesTest(unittest.TestCase):
    def test_moves_java_dirs_to_new_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            _scaffold(project)
            result = _run_rename(
                project,
                "--package", "com.acme.widget",
                "--app-name", "Acme Widget",
                "--app-name-pascal", "AcmeWidget",
                "--app-name-lower", "acmewidget",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            for sub in ("main", "test", "androidTest"):
                old = project / "app" / "src" / sub / "java" / "com" / "example" / "myapp"
                new = project / "app" / "src" / sub / "java" / "com" / "acme" / "widget"
                self.assertFalse(old.exists(), f"{old} should have been removed")
                self.assertTrue(new.is_dir(), f"{new} should exist")


if __name__ == "__main__":
    unittest.main()
