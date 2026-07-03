#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
from io import StringIO
from pathlib import Path
from typing import Any

from rendering.io import write_text_if_changed, write_text_preserving_generated_at
from rendering.ui import render_shell
from workflow_config import active_project_slug


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    item = Path(path)
    try:
        return item.relative_to(ROOT).as_posix()
    except ValueError:
        return str(item)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def matrix_map(project: str) -> dict[str, dict[str, str]]:
    return {row.get("citekey", ""): row for row in read_csv(MATRIX) if project in row.get("project_tags", "")}


def block_index(project: str) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    readers = PROJECTS / project / "literature" / "readers"
    for source_map in sorted(readers.glob("*/source_map.json")):
        data = read_json(source_map)
        citekey = clean(data.get("citekey"))
        if not citekey:
            citekey = source_map.parent.name
        for block in data.get("blocks", []) or []:
            block_id = clean(block.get("block_id"))
            if not block_id:
                continue
            index[(citekey, block_id)] = {
                "citekey": citekey,
                "block_id": block_id,
                "source_id": clean(block.get("source_id")) or f"{citekey}:{block_id}",
                "page": block.get("page"),
                "char_count": block.get("char_count", ""),
                "snippet": clean(block.get("text"))[:220],
                "source_map": rel(source_map),
                "reader_path": rel(source_map.parent / "paper.md"),
            }
    return index


def expand_blocks(value: str) -> list[str]:
    blocks: list[str] = []
    for start, end in re.findall(r"B(\d{4})\s*[-–]\s*B(\d{4})", value):
        start_i = int(start)
        end_i = int(end)
        if end_i >= start_i and end_i - start_i <= 80:
            blocks.extend(f"B{index:04d}" for index in range(start_i, end_i + 1))
    singles = re.findall(r"\bB\d{4}\b", value)
    for block in singles:
        if block not in blocks:
            blocks.append(block)
    return blocks


def parse_markdown_tables(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if cells[0] in {"Claim", "主张"} or "证据" in cells[0]:
            continue
        rows.append(cells)
    return rows


def claim_rows_from_synthesis(project: str) -> list[dict[str, str]]:
    path = PROJECTS / project / "03_literature_synthesis.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    result: list[dict[str, str]] = []
    for cells in parse_markdown_tables(text):
        joined = " | ".join(cells)
        citekeys = re.findall(r"cnki_\d{4}_[a-z0-9]+", joined)
        blocks = expand_blocks(joined)
        if not citekeys or not blocks:
            continue
        result.append(
            {
                "claim": clean(cells[0]),
                "evidence_summary": clean(cells[1]) if len(cells) > 1 else "",
                "citation_cell": clean(cells[2]) if len(cells) > 2 else "",
                "boundary": clean(cells[3]) if len(cells) > 3 else "",
                "citekeys": ";".join(dict.fromkeys(citekeys)),
                "blocks": ";".join(dict.fromkeys(blocks)),
            }
        )
    return result


def build_rows(project: str) -> list[dict[str, str]]:
    papers = matrix_map(project)
    blocks = block_index(project)
    claims = claim_rows_from_synthesis(project)
    rows: list[dict[str, str]] = []
    for claim_index, claim in enumerate(claims, start=1):
        for citekey in claim["citekeys"].split(";"):
            for block_id in claim["blocks"].split(";"):
                block = blocks.get((citekey, block_id), {})
                paper = papers.get(citekey, {})
                page = block.get("page")
                rows.append(
                    {
                        "claim_id": f"C{claim_index:03d}",
                        "claim": claim["claim"],
                        "evidence_summary": claim["evidence_summary"],
                        "citekey": citekey,
                        "title": clean(paper.get("title")),
                        "read_status": clean(paper.get("read_status")),
                        "block_id": block_id,
                        "source_id": clean(block.get("source_id")) or f"{citekey}:{block_id}",
                        "page": str(page) if page else "",
                        "locator_status": "page_located_needs_human_check" if page else "page_pending",
                        "boundary": claim["boundary"],
                        "reader_path": clean(block.get("reader_path")),
                        "source_map": clean(block.get("source_map")),
                        "snippet": clean(block.get("snippet")),
                    }
                )
    if rows:
        return rows
    for (citekey, block_id), block in blocks.items():
        paper = papers.get(citekey, {})
        page = block.get("page")
        rows.append(
            {
                "claim_id": "",
                "claim": "source_block_inventory",
                "evidence_summary": "Reader block available; not yet tied to a manuscript claim.",
                "citekey": citekey,
                "title": clean(paper.get("title")),
                "read_status": clean(paper.get("read_status")),
                "block_id": block_id,
                "source_id": clean(block.get("source_id")),
                "page": str(page) if page else "",
                "locator_status": "page_located_needs_human_check" if page else "page_pending",
                "boundary": "Do not cite until the block is checked against the original PDF.",
                "reader_path": clean(block.get("reader_path")),
                "source_map": clean(block.get("source_map")),
                "snippet": clean(block.get("snippet")),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "claim_id",
        "claim",
        "evidence_summary",
        "citekey",
        "title",
        "read_status",
        "block_id",
        "source_id",
        "page",
        "locator_status",
        "boundary",
        "reader_path",
        "source_map",
        "snippet",
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_text_if_changed(path, buffer.getvalue())


def write_md(path: Path, project: str, rows: list[dict[str, str]], csv_path: Path, html_path: Path) -> None:
    located = sum(1 for row in rows if row["page"])
    lines = [
        f"# Evidence Locator Table - {project}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"CSV: `{rel(csv_path)}`",
        f"HTML: `{rel(html_path)}`",
        "",
        "## Boundary",
        "",
        "- This is a locator and verification workbench, not final manuscript evidence.",
        "- `page_located_needs_human_check` means the extractor found a page number, but the user still needs to verify against the original PDF.",
        "- `page_pending` means the current Reader was created before page-aware extraction or came from a non-page-aware source.",
        "",
        "## Summary",
        "",
        f"- Rows: {len(rows)}",
        f"- Page located: {located}",
        f"- Page pending: {len(rows) - located}",
        "",
        "## Claim Locators",
        "",
        "| Claim | Citekey | Block | Page | Status | Boundary |",
        "|---|---|---|---:|---|---|",
    ]
    for row in rows[:120]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["claim"].replace("|", "/")[:120],
                    f"`{row['citekey']}`",
                    f"`{row['block_id']}`",
                    row["page"] or "待补",
                    row["locator_status"],
                    row["boundary"].replace("|", "/")[:120],
                ]
            )
            + " |"
        )
    write_text_preserving_generated_at(path, "\n".join(lines) + "\n")


def write_html(path: Path, project: str, rows: list[dict[str, str]], csv_path: Path, md_path: Path) -> None:
    located = sum(1 for row in rows if row["page"])
    table_rows = "\n".join(
        f"""
        <tr>
          <td>{html.escape(row['claim'])}<br><span>{html.escape(row['evidence_summary'])}</span></td>
          <td>{html.escape(row['title'] or row['citekey'])}<br><code>{html.escape(row['citekey'])}</code></td>
          <td><code>{html.escape(row['block_id'])}</code><br><span>{html.escape(row['source_id'])}</span></td>
          <td>{html.escape(row['page'] or '待补')}</td>
          <td><code>{html.escape(row['locator_status'])}</code></td>
          <td>{html.escape(row['boundary'])}</td>
        </tr>
        """
        for row in rows[:180]
    )
    body = f"""
    <section class="grid">
      <div class="metric"><b>{len(rows)}</b><span>证据定位行</span></div>
      <div class="metric"><b>{located}</b><span>已有页码</span></div>
      <div class="metric"><b>{len(rows) - located}</b><span>页码待补</span></div>
      <section class="panel">
        <h2>主张-证据-block-page</h2>
        <table>
          <thead><tr><th>主张</th><th>文献</th><th>Block</th><th>页码</th><th>核验状态</th><th>边界</th></tr></thead>
          <tbody>{table_rows or '<tr><td colspan="6">暂无可定位证据。</td></tr>'}</tbody>
        </table>
      </section>
    </section>
"""
    html_text = render_shell(
        title="证据定位表",
        subtitle="把综述主张连接到文献、source block 和页码线索，作为正式引用前的定位工作台。",
        current="证据定位",
        body=body,
        output=path,
        module="证据",
        meta=f"{html.escape(project)} · Generated {html.escape(dt.datetime.now().isoformat(timespec='seconds'))}",
        primary_action=f'<a class="button primary" href="{html.escape(csv_path.name)}">CSV 数据</a>',
        footer="Generated by scripts/build_evidence_locators.py.",
    )
    write_text_preserving_generated_at(path, html_text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a project-level evidence locator table from Readers and synthesis claims.")
    parser.add_argument("--project", default=active_project_slug())
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    out_dir = project / "literature"
    csv_path = out_dir / "evidence_locator_table.csv"
    md_path = out_dir / "evidence_locator_table.md"
    html_path = out_dir / "evidence_locator_table.html"

    rows = build_rows(args.project)
    write_csv(csv_path, rows)
    write_md(md_path, args.project, rows, csv_path, html_path)
    write_html(html_path, args.project, rows, csv_path, md_path)
    print(f"Wrote evidence locator CSV: {csv_path}")
    print(f"Wrote evidence locator markdown: {md_path}")
    print(f"Wrote evidence locator HTML: {html_path}")
    print(f"Rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
