#!/usr/bin/env python3
"""Build the static Surge mirror from the versioned cloud files."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "2.6.4"
OUTPUT = ROOT / "dist"


def main() -> None:
    if not SOURCE.is_dir() or SOURCE.is_symlink():
        raise SystemExit("missing cloud source directory")

    # Only the fixed, repository-local dist path may be replaced.
    if OUTPUT.resolve() != (ROOT / "dist").resolve():
        raise SystemExit("invalid output path")
    if OUTPUT.exists():
        if OUTPUT.is_symlink():
            raise SystemExit("refusing symlink output")
        shutil.rmtree(OUTPUT)

    files: dict[str, str] = {}
    for source in sorted(SOURCE.rglob("*")):
        if source.is_symlink():
            raise SystemExit(f"refusing symlink: {source}")
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT)
        data = source.read_bytes()
        if source.suffix.lower() == ".json":
            json.loads(data)
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        files[relative.as_posix()] = hashlib.sha256(data).hexdigest()

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    status = {"commit": commit, "files": files}
    (OUTPUT / "mirror-status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUTPUT / "index.html").write_text(
        "<!doctype html><title>Cloud mirror</title><p>Cloud mirror online.</p>\n",
        encoding="utf-8",
    )
    print(f"MIRROR_FILES={len(files)} COMMIT={commit}")


if __name__ == "__main__":
    main()
