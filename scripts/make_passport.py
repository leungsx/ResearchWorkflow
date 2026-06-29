#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
SKIP_NAMES = {".DS_Store", "material_passport.json", "checksums.csv"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        yield path


def make_passport(root: Path) -> dict:
    files = []
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        files.append(
            {
                "path": rel,
                "bytes": stat.st_size,
                "modified_at": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "sha256": sha256(path),
            }
        )
    return {
        "schema": "ResearchWorkflow.MaterialPassport.v1",
        "root": str(root),
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "file_count": len(files),
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a material passport with checksums.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="Project slug under projects/")
    group.add_argument("--root", type=Path, help="Arbitrary root path")
    args = parser.parse_args()

    root = PROJECTS / args.project if args.project else args.root
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    passport_dir = root / "passport"
    passport_dir.mkdir(parents=True, exist_ok=True)
    passport = make_passport(root)

    json_path = passport_dir / "material_passport.json"
    csv_path = passport_dir / "checksums.csv"
    json_path.write_text(json.dumps(passport, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "modified_at", "sha256"])
        writer.writeheader()
        writer.writerows(passport["files"])

    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(f"Files recorded: {passport['file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

