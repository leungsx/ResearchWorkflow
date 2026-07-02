#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from literature_matrix_schema import matrix_fields


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
MATRIX_FIELDS = matrix_fields()


def load_existing(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as handle:
        return {row["citekey"] for row in csv.DictReader(handle) if row.get("citekey")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Append OpenAlex search results to literature_matrix.csv.")
    parser.add_argument("--csv", dest="csv_path", type=Path, required=True)
    parser.add_argument("--tag", default="", help="Optional project tag to apply to imported rows")
    args = parser.parse_args()

    if not args.csv_path.exists():
        raise FileNotFoundError(args.csv_path)

    MATRIX.parent.mkdir(parents=True, exist_ok=True)
    if not MATRIX.exists():
        with MATRIX.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
            writer.writeheader()

    existing = load_existing(MATRIX)
    rows = list(csv.DictReader(args.csv_path.open(encoding="utf-8")))
    imported = 0
    skipped = 0
    with MATRIX.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
        for row in rows:
            citekey = row.get("citekey", "")
            if not citekey or citekey in existing:
                skipped += 1
                continue
            writer.writerow(
                {
                    "citekey": citekey,
                    "title": row.get("title", ""),
                    "year": row.get("year", ""),
                    "authors": row.get("authors", ""),
                    "doi": row.get("doi", ""),
                    "source": row.get("source", ""),
                    "source_database": row.get("source_database", "OpenAlex"),
                    "language": row.get("language", ""),
                    "publication_type": row.get("publication_type", ""),
                    "cssci_status": row.get("cssci_status", ""),
                    "project_tags": args.tag,
                    "theory": "",
                    "methods": "",
                    "data": "",
                    "core_findings": row.get("abstract", ""),
                    "limitations": "",
                    "usable_quotes": "",
                    "chinese_reference_translation": row.get("chinese_reference_translation", ""),
                    "target_journal_relevance": row.get("target_journal_relevance", ""),
                    "read_status": "unread",
                    "note_path": "",
                    "pdf_path": "",
                }
            )
            existing.add(citekey)
            imported += 1

    print(f"Imported {imported} rows into {MATRIX}")
    print(f"Skipped {skipped} existing or invalid rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
