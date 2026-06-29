#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VAULT_LIT = ROOT / "vault" / "01_Literature"
TEMPLATE = ROOT / "vault" / "99_Templates" / "Paper Note.md"


def find_row(csv_path: Path, citekey: str) -> dict[str, str]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    for row in rows:
        if row.get("citekey") == citekey:
            return row
    available = ", ".join(row.get("citekey", "") for row in rows[:10])
    raise KeyError(f"Citekey not found: {citekey}. First available: {available}")


def render(template: str, row: dict[str, str]) -> str:
    values = {
        "citekey": row.get("citekey", ""),
        "title": row.get("title", ""),
        "year": row.get("year", ""),
        "authors": row.get("authors", ""),
        "doi": row.get("doi", ""),
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value.replace('"', '\\"'))
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an Obsidian paper note from a search CSV row.")
    parser.add_argument("--csv", dest="csv_path", type=Path, required=True)
    parser.add_argument("--citekey", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    row = find_row(args.csv_path, args.citekey)
    VAULT_LIT.mkdir(parents=True, exist_ok=True)
    dest = VAULT_LIT / f"{args.citekey}.md"
    if dest.exists() and not args.overwrite:
        raise FileExistsError(f"Note already exists: {dest}")
    content = render(TEMPLATE.read_text(encoding="utf-8"), row)
    content += "\n## Links\n\n"
    if row.get("doi"):
        content += f"- DOI: https://doi.org/{row['doi']}\n"
    if row.get("pdf_url"):
        content += f"- Open PDF: {row['pdf_url']}\n"
    if row.get("openalex_id"):
        content += f"- OpenAlex: {row['openalex_id']}\n"
    dest.write_text(content, encoding="utf-8")
    print(f"Created note: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

