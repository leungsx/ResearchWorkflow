#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "library" / "search_results"
BIB_PATH = ROOT / "library" / "bib" / "references.bib"


FIELDS = [
    "citekey",
    "title",
    "year",
    "authors",
    "doi",
    "openalex_id",
    "source",
    "cited_by_count",
    "oa_status",
    "oa_url",
    "pdf_url",
    "abstract",
]


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("_") or "search"


def abstract_from_inverted_index(index: dict | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, locs in index.items():
        for pos in locs:
            positions.append((pos, word))
    return " ".join(word for _, word in sorted(positions))


def make_citekey(item: dict) -> str:
    year = item.get("publication_year") or "n.d."
    authorships = item.get("authorships") or []
    if authorships:
        surname = (authorships[0].get("author", {}).get("display_name") or "Anon").split()[-1]
    else:
        surname = "Anon"
    title = item.get("title") or "untitled"
    first_word = re.sub(r"[^A-Za-z0-9]+", "", title.split()[0] if title.split() else "Work")
    key = f"{surname}{year}{first_word}"
    return re.sub(r"[^A-Za-z0-9_:-]+", "", key)


def format_authors(authorships: list[dict]) -> str:
    names = []
    for authorship in authorships:
        name = authorship.get("author", {}).get("display_name")
        if name:
            names.append(name)
    return "; ".join(names)


def bibtex_escape(value: str) -> str:
    return value.replace("{", "\\{").replace("}", "\\}")


def to_bibtex(row: dict[str, str]) -> str:
    fields = {
        "title": row["title"],
        "author": row["authors"].replace("; ", " and "),
        "year": row["year"],
        "doi": row["doi"],
        "url": row["oa_url"] or row["openalex_id"],
    }
    lines = [f"@article{{{row['citekey']},"]
    for key, value in fields.items():
        if value:
            lines.append(f"  {key} = {{{bibtex_escape(value)}}},")
    lines.append("}")
    return "\n".join(lines)


def existing_bib_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"@\w+\{([^,\s]+)", text))


def append_unique_bibtex(path: Path, rows: list[dict[str, str]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = existing_bib_keys(path)
    entries = []
    for row in rows:
        citekey = row["citekey"]
        if citekey in existing:
            continue
        entries.append(to_bibtex(row))
        existing.add(citekey)
    if entries:
        prefix = "\n\n" if path.exists() and path.read_text(encoding="utf-8", errors="ignore").strip() else ""
        with path.open("a", encoding="utf-8") as handle:
            handle.write(prefix + "\n\n".join(entries) + "\n")
    return len(entries)


def fetch_openalex(query: str, limit: int, mailto: str | None) -> list[dict]:
    params = {
        "search": query,
        "per-page": str(min(limit, 200)),
        "sort": "cited_by_count:desc",
    }
    if mailto:
        params["mailto"] = mailto
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"ResearchWorkflow/1.0 ({mailto or 'no-email'})"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("results", [])[:limit]


def normalize_item(item: dict) -> dict[str, str]:
    best_oa = item.get("best_oa_location") or {}
    open_access = item.get("open_access") or {}
    primary = item.get("primary_location") or {}
    source = (primary.get("source") or {}).get("display_name") or ""
    doi = item.get("doi") or ""
    row = {
        "citekey": make_citekey(item),
        "title": item.get("title") or "",
        "year": str(item.get("publication_year") or ""),
        "authors": format_authors(item.get("authorships") or []),
        "doi": doi.replace("https://doi.org/", ""),
        "openalex_id": item.get("id") or "",
        "source": source,
        "cited_by_count": str(item.get("cited_by_count") or 0),
        "oa_status": open_access.get("oa_status") or "",
        "oa_url": open_access.get("oa_url") or "",
        "pdf_url": best_oa.get("pdf_url") or "",
        "abstract": abstract_from_inverted_index(item.get("abstract_inverted_index")),
    }
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Search OpenAlex and save metadata.")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--mailto", help="Optional polite email for OpenAlex")
    parser.add_argument("--output", type=Path, help="Output CSV path")
    parser.add_argument("--no-bib", action="store_true", help="Do not write BibTeX")
    args = parser.parse_args()

    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    rows = [normalize_item(item) for item in fetch_openalex(args.query, args.limit, args.mailto)]
    output = args.output or SEARCH_DIR / f"{safe_filename(args.query)}.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    search_bib = output.with_suffix(".bib")
    if not args.no_bib:
        search_bib.write_text("\n\n".join(to_bibtex(row) for row in rows) + "\n", encoding="utf-8")
        appended = append_unique_bibtex(BIB_PATH, rows)

    print(f"Saved {len(rows)} records to {output}")
    if not args.no_bib:
        print(f"Wrote search BibTeX to {search_bib}")
        print(f"Appended {appended} new BibTeX entries to {BIB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
