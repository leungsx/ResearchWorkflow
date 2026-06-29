#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWEEP_DIR = ROOT / "vault" / "07_Codex_Logs" / "file_sweeps"

EXCLUDE_PARTS = {
    "__pycache__",
    ".git",
    ".obsidian",
    "backups",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".DS_Store",
}


def parse_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return dt.date.today()


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return True
    if path.name in EXCLUDE_SUFFIXES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def classify(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    if not parts:
        return "root"
    if parts[0] == "vault":
        return "obsidian"
    if parts[0] == "codex":
        return "codex"
    if parts[0] == "scripts":
        return "automation"
    if parts[0] == "projects":
        return "project"
    if parts[0] == "library":
        return "library"
    if parts[0] == "docs":
        return "docs"
    return parts[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="List files modified on a date for Codex daily archive.")
    parser.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--output", type=Path, help="Optional output markdown path")
    args = parser.parse_args()

    day = parse_date(args.date)
    start = dt.datetime.combine(day, dt.time.min).timestamp()
    end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time.min).timestamp()

    rows: list[tuple[str, Path, int]] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        stat = path.stat()
        if start <= stat.st_mtime < end:
            rows.append((classify(path), path.relative_to(ROOT), stat.st_size))

    rows.sort(key=lambda item: (item[0], str(item[1])))
    output = args.output or SWEEP_DIR / f"{day.isoformat()}-file-sweep.md"
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# File Sweep - {day.isoformat()}",
        "",
        f"Root: `{ROOT}`",
        f"Files modified: {len(rows)}",
        "",
    ]
    current = None
    for group, rel, size in rows:
        if group != current:
            current = group
            lines.extend(["", f"## {group}", ""])
        lines.append(f"- `{rel}` ({size} bytes)")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote file sweep: {output}")
    print(f"Files modified: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
