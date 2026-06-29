#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"
INDEX_HTML = BACKUP_DIR / "index.html"

INCLUDE_ROOT_FILES = {
    "Makefile",
    "README.md",
    ".gitignore",
    "requirements.txt",
    "study_dashboard.html",
    "workflow_health.html",
}

INCLUDE_DIRS = {
    "codex",
    "config",
    "docs",
    "knowledge_cards",
    "knowledge_graph",
    "logs",
    "paper_reading",
    "projects",
    "prompts",
    "scripts",
    "vault",
}

INCLUDE_LIBRARY_FILES = {
    "library/literature_matrix.csv",
    "library/relations.csv",
    "library/chinese_literature_import_template.csv",
}

EXCLUDE_PARTS = {
    ".git",
    ".obsidian",
    "__pycache__",
    ".ipynb_checkpoints",
    "backups",
}

EXCLUDE_SUFFIXES = {
    ".DS_Store",
    ".pyc",
    ".pdf",
    ".caj",
    ".kdh",
    ".zip",
    ".docx",
    ".xlsx",
    ".xls",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".mp4",
    ".mov",
}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return True
    if path.name in EXCLUDE_SUFFIXES or path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if rel.parts[:3] == ("projects", rel.parts[1] if len(rel.parts) > 1 else "", "data"):
        return True
    if rel.parts[:2] in {("library", "pdfs"), ("library", "papers"), ("library", "text")}:
        return True
    return False


def include_file(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    first = rel.split("/", 1)[0]
    if rel in INCLUDE_ROOT_FILES or rel in INCLUDE_LIBRARY_FILES:
        return True
    return first in INCLUDE_DIRS


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if include_file(path):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def write_index() -> None:
    zips = sorted(BACKUP_DIR.glob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    rows = "\n".join(
        f"<tr><td><a href=\"{path.name}\">{path.name}</a></td><td>{path.stat().st_size / 1024:.1f} KB</td><td>{dt.datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}</td></tr>"
        for path in zips[:30]
    )
    INDEX_HTML.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ResearchWorkflow Backups</title>
  <style>
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; background:#f5f7fa; color:#182026; }}
    .wrap {{ max-width:980px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid #d9e2ea; border-radius:12px; overflow:hidden; }}
    th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #d9e2ea; }}
    th {{ color:#61707d; }}
    a {{ color:#2463eb; text-decoration:none; }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>ResearchWorkflow Backups</h1>
    <p>关键研究状态、脚本、规范和浏览入口的轻量备份。PDF、原始数据、缓存和大型二进制文件不在此包内。</p>
    <table><thead><tr><th>备份包</th><th>大小</th><th>时间</th></tr></thead><tbody>{rows}</tbody></table>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def prune_backups(keep: int) -> int:
    if keep < 1:
        raise ValueError("--keep must be at least 1 when pruning backups")
    zips = sorted(BACKUP_DIR.glob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    removed = 0
    for path in zips[keep:]:
        path.unlink()
        removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a lightweight ResearchWorkflow backup zip.")
    parser.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--note", default="", help="Optional note stored in the manifest.")
    parser.add_argument("--keep", type=int, help="After creating a backup, keep only the newest N backup zips.")
    parser.add_argument("--prune-only", action="store_true", help="Do not create a new backup; only prune with --keep.")
    args = parser.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if args.prune_only:
        if not args.keep:
            raise SystemExit("--prune-only requires --keep N")
        removed = prune_backups(args.keep)
        write_index()
        print(f"Pruned backups: removed {removed}, kept newest {args.keep}")
        print(f"Backup index: {INDEX_HTML}")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"researchworkflow-critical-{stamp}.zip"
    files = backup_files()
    manifest = {
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "date": day.isoformat(),
        "root": str(ROOT),
        "note": args.note,
        "policy": "critical text/config/html state only; excludes PDFs, raw data, caches, and large binaries",
        "file_count": len(files),
        "files": [],
    }
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            arcname = path.relative_to(ROOT).as_posix()
            archive.write(path, arcname)
            manifest["files"].append(
                {
                    "path": arcname,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        archive.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    removed = 0
    if args.keep:
        removed = prune_backups(args.keep)
    write_index()
    print(f"Wrote backup: {target}")
    print(f"Files included: {len(files)}")
    if args.keep:
        print(f"Pruned backups: removed {removed}, kept newest {args.keep}")
    print(f"Backup index: {INDEX_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
