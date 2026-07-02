#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from literature_matrix_schema import read_simple_schema
from workflow_config import active_project_slug


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
SCHEMA = ROOT / "schemas" / "claim_evidence_links.schema.yaml"


def clean(value: str | None) -> str:
    return (value or "").strip()


def risk_for(row: dict[str, str]) -> str:
    risks: list[str] = []
    if clean(row.get("read_status")) not in {"human-read", "verified", "claim-linked", "manuscript-cited"}:
        risks.append("needs_human_validation")
    if clean(row.get("locator_status")) == "page_pending":
        risks.append("page_locator_pending")
    if not clean(row.get("page")):
        risks.append("page_missing")
    return ";".join(risks) or "low"


def build_rows(source: Path) -> list[dict[str, str]]:
    if not source.exists():
        return []
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    with source.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            claim_id = clean(row.get("claim_id"))
            citekey = clean(row.get("citekey"))
            source_block_id = clean(row.get("source_id")) or clean(row.get("block_id"))
            key = (claim_id, citekey, source_block_id)
            if not claim_id or not citekey or not source_block_id or key in seen:
                continue
            seen.add(key)
            output.append(
                {
                    "claim_id": claim_id,
                    "claim_text": clean(row.get("claim")),
                    "citekey": citekey,
                    "evidence_type": "literature",
                    "source_block_id": source_block_id,
                    "page": clean(row.get("page")),
                    "locator_status": clean(row.get("locator_status")),
                    "read_status": clean(row.get("read_status")),
                    "strength": "candidate",
                    "risk": risk_for(row),
                    "used_in_manuscript": "false",
                    "source_path": clean(row.get("reader_path")),
                }
            )
    return output


def write_markdown(rows: list[dict[str, str]], output: Path, csv_path: Path) -> None:
    lines = [
        "# Structured Claim-Evidence Links",
        "",
        "This file is generated from the evidence locator table. Edit the CSV when a candidate source becomes manuscript evidence.",
        "",
        f"- CSV: `{csv_path.relative_to(ROOT)}`",
        f"- Rows: {len(rows)}",
        "",
        "| Claim | Citekey | Source block | Read status | Locator | Used in manuscript | Risk |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in rows[:120]:
        lines.append(
            "| {claim_id} | `{citekey}` | `{source_block_id}` | `{read_status}` | {locator_status} | {used_in_manuscript} | {risk} |".format(
                **row
            )
        )
    if len(rows) > 120:
        lines.append(f"| ... | ... | ... | ... | ... | ... | {len(rows) - 120} more rows omitted |")
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build structured claim-evidence links from evidence locators.")
    parser.add_argument("--project", default=active_project_slug())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    source = args.input or project / "literature" / "evidence_locator_table.csv"
    output = args.output or project / "evidence" / "claim_evidence_links.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = read_simple_schema(SCHEMA).get("field_order", [])
    if not isinstance(fields, list) or not fields:
        raise RuntimeError(f"Missing field_order in {SCHEMA}")
    rows = build_rows(source)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[str(field) for field in fields], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    md_path = output.with_suffix(".md")
    write_markdown(rows, md_path, output)
    print(f"Wrote claim-evidence links: {output}")
    print(f"Wrote claim-evidence summary: {md_path}")
    print(f"Rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
