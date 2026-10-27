#!/usr/bin/env python3
"""Build TRINETRA_prototype.zip at the project root.

Zips the trinetra/ directory but excludes build/cache artifacts and the
regenerable SQLite database, while KEEPING source, docs, scripts outputs, and
the generated screenshots. Run:  python3 scripts/make_zip.py
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "trinetra"
OUT = ROOT / "TRINETRA_prototype.zip"

# Directory names excluded anywhere in the tree.
EXCLUDE_DIRS = {"node_modules", "dist", ".vite", "__pycache__", ".git"}
# File suffixes excluded.
EXCLUDE_SUFFIXES = {".pyc"}
# Specific filenames excluded (the db regenerates via generate_data.py).
EXCLUDE_NAMES = {"trinetra.db", ".DS_Store"}


def should_skip_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS


def should_skip_file(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Source directory not found: {SRC}")

    if OUT.exists():
        OUT.unlink()

    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(SRC):
            # Prune excluded directories in-place so os.walk skips them.
            dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
            for fn in filenames:
                fp = Path(dirpath) / fn
                if should_skip_file(fp):
                    continue
                # Store paths relative to the project root so the zip contains trinetra/...
                arcname = fp.relative_to(ROOT)
                zf.write(fp, arcname)
                count += 1

    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"Wrote {OUT}")
    print(f"  files: {count}")
    print(f"  size : {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
