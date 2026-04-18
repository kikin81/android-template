#!/usr/bin/env python3
"""One-shot rename script for the android-template.

Rewrites the placeholder package (``com.example.myapp``) and app-name variants
(``My App`` / ``MyApplication`` / ``MyApp`` / ``myapp``) across the repo
produced by ``android create empty-activity``. Intended to be run exactly once,
immediately after cloning from the template.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Placeholders baked into the `android create empty-activity` output.
# Note: `MyApplication` is the actual class/theme prefix the generator emits
# (e.g. `MyApplicationTheme`, `Theme.MyApplication`); bare `MyApp` does not
# appear in current output but is kept as a defensive fallback. `MyApplication`
# must be substituted BEFORE `MyApp` (longest-match-first) or
# `MyApplicationTheme` would become `{pascal}licationTheme`.
OLD_PACKAGE_DOTTED = "com.example.myapp"
OLD_PACKAGE_SLASHED = "com/example/myapp"
OLD_APP_NAME = "My App"
OLD_APPLICATION = "MyApplication"
OLD_PASCAL = "MyApp"
OLD_LOWER = "myapp"

PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
PASCAL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
LOWER_RE = re.compile(r"^[a-z][a-z0-9]*$")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename the template's placeholder identifiers in one shot.",
    )
    parser.add_argument("--package", required=True, help="e.g. com.acme.widget")
    parser.add_argument("--app-name", required=True, help='e.g. "Acme Widget"')
    parser.add_argument("--app-name-pascal", required=True, help="e.g. AcmeWidget")
    parser.add_argument("--app-name-lower", required=True, help="e.g. acmewidget")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-script", action="store_true")
    args = parser.parse_args(argv)

    if not PACKAGE_RE.match(args.package):
        parser.error("--package must be a dotted lowercase Java package (e.g. com.acme.widget)")
    if not args.app_name.strip():
        parser.error("--app-name must be non-empty")
    if not PASCAL_RE.match(args.app_name_pascal):
        parser.error("--app-name-pascal must start with uppercase letter, then alphanumerics only")
    if not LOWER_RE.match(args.app_name_lower):
        parser.error("--app-name-lower must start with lowercase letter, then lowercase alphanumerics only")

    return args


def _preflight(repo: Path) -> None:
    java_root = repo / "app" / "src" / "main" / "java" / "com" / "example" / "myapp"
    if not java_root.is_dir():
        raise SystemExit(
            f"pre-flight failed: expected directory {java_root} "
            f"(no com.example.myapp template markers — already renamed?)"
        )


def _move_dirs(repo: Path, package: str) -> None:
    new_parts = package.split(".")
    for sub in ("main", "test", "androidTest"):
        old_root = repo / "app" / "src" / sub / "java" / "com" / "example" / "myapp"
        if not old_root.exists():
            continue
        new_root = repo / "app" / "src" / sub / "java" / Path(*new_parts)
        new_root.parent.mkdir(parents=True, exist_ok=True)
        old_root.rename(new_root)
    # Clean up now-empty `com/example/` stub parents.
    for sub in ("main", "test", "androidTest"):
        stub = repo / "app" / "src" / sub / "java" / "com" / "example"
        if stub.exists() and not any(stub.iterdir()):
            stub.rmdir()
            parent = stub.parent
            if parent.name == "com" and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo = Path.cwd()
    _preflight(repo)
    _move_dirs(repo, args.package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
