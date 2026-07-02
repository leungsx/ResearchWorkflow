#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import extract_pdf_text


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"
LIBRARY_READERS = ROOT / "library" / "readers"


def load_rows(matrix: Path) -> list[dict[str, str]]:
    if not matrix.exists():
        return []
    with matrix.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_row(rows: list[dict[str, str]], citekey: str, title: str) -> dict[str, str]:
    if citekey:
        for row in rows:
            if row.get("citekey") == citekey:
                return row
        raise KeyError(f"Citekey not found: {citekey}")
    if title:
        candidates = [row for row in rows if title in row.get("title", "")]
        if len(candidates) == 1:
            return candidates[0]
        if not candidates:
            raise KeyError(f"Title not found: {title}")
        raise KeyError(f"Multiple title matches found; use --citekey. Matches: {[row.get('citekey') for row in candidates]}")
    raise ValueError("Use --citekey or --title.")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_page_text(page: int | None, text: str, max_chars: int = 1200) -> list[dict[str, Any]]:
    paragraphs = [clean(part) for part in re.split(r"\n\s*\n+", text) if clean(part)]
    blocks: list[dict[str, Any]] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if current and current_len + len(paragraph) + 2 > max_chars:
            blocks.append({"text": "\n\n".join(current), "page": page})
            current = []
            current_len = 0
        if len(paragraph) > max_chars:
            if current:
                blocks.append({"text": "\n\n".join(current), "page": page})
                current = []
                current_len = 0
            for start in range(0, len(paragraph), max_chars):
                blocks.append({"text": paragraph[start : start + max_chars], "page": page})
            continue
        current.append(paragraph)
        current_len += len(paragraph) + 2
    if current:
        blocks.append({"text": "\n\n".join(current), "page": page})
    return blocks


def split_blocks(text: str, max_chars: int = 1200) -> list[dict[str, Any]]:
    return split_page_text(None, text, max_chars=max_chars)


def split_page_blocks(pages: list[tuple[int, str]], max_chars: int = 1200) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for page, text in pages:
        blocks.extend(split_page_text(page, text, max_chars=max_chars))
    return blocks


def resolve_source(row: dict[str, str], pdf: str, text: str) -> tuple[Path, str]:
    if text:
        return Path(text), "text"
    source = pdf or row.get("pdf_path", "")
    if source:
        return Path(source), "pdf"
    raise ValueError("Provide --pdf/--text, or set pdf_path in the literature matrix.")


def read_source_blocks(source: Path, source_type: str) -> list[dict[str, Any]]:
    if not source.exists():
        raise FileNotFoundError(source)
    if source_type == "text":
        return split_blocks(source.read_text(encoding="utf-8", errors="ignore"))
    return split_page_blocks(extract_pdf_text.extract_pages(source))


def output_dir(project: str, citekey: str, output: Path | None) -> Path:
    if output:
        return output
    if project:
        return PROJECTS / project / "literature" / "readers" / citekey
    return LIBRARY_READERS / citekey


def render_paper(row: dict[str, str], blocks: list[dict[str, Any]], source: Path, source_type: str) -> str:
    citekey = row.get("citekey", "")
    title = row.get("title", "")
    lines = [
        f"# Source-Grounded Reader - {title}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Citekey: `{citekey}`",
        f"Source file: `{source}`",
        f"Source type: `{source_type}`",
        f"Current read_status: `{row.get('read_status') or 'blank'}`",
        "",
        "## Use Boundary",
        "",
        "- This file is source-grounded extraction, not a claim that the paper has been human-read.",
        "- Do not use it as manuscript evidence until the relevant block has been read and checked.",
        "- After real reading, update `read_status` in `library/literature_matrix.csv` to `human-read` or `verified`.",
        "",
        "## Metadata",
        "",
        f"- Title: {title or '未记录'}",
        f"- Authors: {row.get('authors') or '未记录'}",
        f"- Year: {row.get('year') or '未记录'}",
        f"- Source: {row.get('source') or '未记录'}",
        f"- Database: {row.get('source_database') or '未记录'}",
        f"- DOI: {row.get('doi') or '未记录'}",
        "",
        "## Extracted Blocks",
        "",
    ]
    for index, block in enumerate(blocks, start=1):
        block_id = f"B{index:04d}"
        page = block.get("page")
        page_text = str(page) if page else "unknown from current extractor"
        lines.extend(
            [
                f"### {block_id}",
                "",
                f"- Source ID: `{citekey}:{block_id}`",
                f"- Page: {page_text}",
                "",
                str(block.get("text", "")),
                "",
            ]
        )
    lines.extend(
        [
            "## Reading Notes",
            "",
            "- Summary after human reading:",
            "- Innovation / value after human reading:",
            "- Method details after human reading:",
            "- Usable evidence block IDs:",
            "- Limitations and uncertainty:",
            "",
        ]
    )
    return "\n".join(lines)


def source_map(row: dict[str, str], blocks: list[dict[str, Any]], source: Path, source_type: str) -> dict:
    citekey = row.get("citekey", "")
    return {
        "schema": "ResearchWorkflow.SourceMap.v1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "citekey": citekey,
        "title": row.get("title", ""),
        "source_file": str(source),
        "source_type": source_type,
        "extraction_confidence": "text_extracted_needs_human_check",
        "blocks": [
            {
                "block_id": f"B{index:04d}",
                "source_id": f"{citekey}:B{index:04d}",
                "page": block.get("page"),
                "block_type": "text",
                "char_count": len(str(block.get("text", ""))),
                "text": str(block.get("text", "")),
            }
            for index, block in enumerate(blocks, start=1)
        ],
    }


def render_notes(row: dict[str, str], source: Path, source_type: str, block_count: int) -> str:
    return "\n".join(
        [
            "# Translation And Extraction Notes",
            "",
            f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
            f"Citekey: `{row.get('citekey', '')}`",
            f"Source file: `{source}`",
            f"Source type: `{source_type}`",
            f"Extracted blocks: {block_count}",
            "",
            "## Boundary",
            "",
            "- The source file must come from legal CNKI/institutional/library access.",
            "- This reader does not automatically mark the paper as human-read.",
            "- Page numbers are captured when the PDF extraction backend exposes page-aware text blocks.",
            "- Page locators still require human checking against the original PDF before manuscript citation.",
            "- Figures and tables are not extracted in this deterministic v1 reader.",
            "",
            "## Human Reading To Complete",
            "",
            "- [ ] Check extraction quality against the original paper.",
            "- [ ] Record important block IDs for claims.",
            "- [ ] Fill summary, method, innovation, limitation, and usable evidence notes in `paper.md`.",
            "- [ ] Update `read_status` only after actual reading.",
            "",
        ]
    )


def update_matrix(matrix: Path, citekey: str, paper_path: Path, source: Path, source_type: str) -> None:
    rows = load_rows(matrix)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    changed = False
    for row in rows:
        if row.get("citekey") != citekey:
            continue
        row["note_path"] = str(paper_path)
        if source_type == "pdf":
            row["pdf_path"] = str(source)
        changed = True
    if changed:
        with matrix.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic source-grounded reader package for a paper.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--project", default="", help="Project slug; outputs to projects/<slug>/literature/readers/<citekey>")
    parser.add_argument("--citekey", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--pdf", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--update-matrix", action="store_true", help="Write note_path/pdf_path back to the literature matrix without changing read_status")
    args = parser.parse_args()

    if args.project and not (PROJECTS / args.project).exists():
        raise FileNotFoundError(PROJECTS / args.project)

    row = find_row(load_rows(args.matrix), args.citekey, args.title)
    citekey = row.get("citekey", "")
    source, source_type = resolve_source(row, args.pdf, args.text)
    blocks = read_source_blocks(source, source_type)
    if not blocks:
        raise RuntimeError("No text blocks extracted from source.")

    target = output_dir(args.project, citekey, args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "assets").mkdir(exist_ok=True)
    paper_path = target / "paper.md"
    paper_path.write_text(render_paper(row, blocks, source, source_type), encoding="utf-8")
    (target / "source_map.json").write_text(json.dumps(source_map(row, blocks, source, source_type), ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "translation_notes.md").write_text(render_notes(row, source, source_type, len(blocks)), encoding="utf-8")
    if args.update_matrix:
        update_matrix(args.matrix, citekey, paper_path, source, source_type)

    print(f"Wrote reader package: {target}")
    print(f"Blocks extracted: {len(blocks)}")
    print("Read status was not changed automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
