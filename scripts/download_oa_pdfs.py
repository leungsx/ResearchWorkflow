#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_DIR = ROOT / "library" / "search_results"
PDF_DIR = ROOT / "library" / "papers"


def latest_search_csv() -> Path:
    files = sorted(DEFAULT_CSV_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No search CSV found. Run literature_search.py first.")
    return files[0]


def download(url: str, dest: Path, user_agent: str) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()
    if b"%PDF" not in data[:1024] and "pdf" not in content_type.lower():
        raise ValueError(f"Downloaded content does not look like a PDF: {content_type}")
    dest.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download open-access PDFs from search results.")
    parser.add_argument("--csv", dest="csv_path", type=Path, help="Search CSV path")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--user-agent", default="ResearchWorkflow/1.0")
    args = parser.parse_args()

    csv_path = args.csv_path or latest_search_csv()
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if args.limit:
        rows = rows[: args.limit]

    ok = 0
    skipped = 0
    failed = 0
    for row in rows:
        url = (row.get("pdf_url") or "").strip()
        citekey = (row.get("citekey") or "paper").strip()
        if not url:
            skipped += 1
            continue
        dest = PDF_DIR / f"{citekey}.pdf"
        if dest.exists():
            print(f"[SKIP] exists: {dest.name}")
            skipped += 1
            continue
        try:
            download(url, dest, args.user_agent)
            print(f"[OK] {dest.name}")
            ok += 1
        except Exception as exc:
            print(f"[FAIL] {citekey}: {exc}")
            failed += 1
        time.sleep(args.sleep)

    print(f"Downloaded: {ok}; skipped: {skipped}; failed: {failed}")
    print("Policy reminder: use this only for open-access or otherwise authorized PDFs.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

