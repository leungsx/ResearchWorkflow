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
CRITICAL_USAGE_STATUSES = {"claim-linked", "manuscript-cited", "submission-evidence"}
EVIDENCE_USAGE_STATUSES = {"not-used", "candidate", *CRITICAL_USAGE_STATUSES}
READY_READ_STATUSES = {"human-read", "verified"}


def clean(value: str | None) -> str:
    return (value or "").strip()


def truthy(value: str | None) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "是"}


def row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (clean(row.get("claim_id")), clean(row.get("citekey")), clean(row.get("source_block_id")))


def evidence_usage_status(row: dict[str, str], default: str = "candidate") -> str:
    explicit = clean(row.get("evidence_usage_status"))
    if explicit in EVIDENCE_USAGE_STATUSES:
        return explicit
    read_status = clean(row.get("read_status"))
    if read_status in CRITICAL_USAGE_STATUSES:
        return read_status
    if truthy(row.get("used_in_manuscript")):
        return "manuscript-cited"
    return default


def manuscript_flag(status: str, fallback: str | None = None) -> str:
    if fallback is not None and truthy(fallback):
        return "true"
    return "true" if status in {"manuscript-cited", "submission-evidence"} else "false"


def risk_for(row: dict[str, str]) -> str:
    risks: list[str] = []
    if clean(row.get("read_status")) not in READY_READ_STATUSES:
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
                    "evidence_usage_status": "candidate",
                    "strength": "candidate",
                    "risk": risk_for(row),
                    "used_in_manuscript": "false",
                    "source_path": clean(row.get("reader_path")),
                }
            )
    return output


def normalize_row(row: dict[str, str], fields: list[str], default_usage: str = "candidate") -> dict[str, str]:
    normalized = {field: clean(row.get(field)) for field in fields}
    status = evidence_usage_status(row, default=default_usage)
    normalized["evidence_usage_status"] = status
    normalized["used_in_manuscript"] = manuscript_flag(status, row.get("used_in_manuscript"))
    if clean(row.get("read_status")) in CRITICAL_USAGE_STATUSES:
        normalized["read_status"] = "verified"
    if not normalized.get("evidence_type"):
        normalized["evidence_type"] = "literature"
    if not normalized.get("strength"):
        normalized["strength"] = "candidate"
    if not normalized.get("risk"):
        normalized["risk"] = "needs_human_validation"
    return normalized


def sync_confirmed_links(candidates: list[dict[str, str]], existing_path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not existing_path.exists():
        return [normalize_row(row, fields, default_usage="candidate") for row in candidates]
    existing: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    with existing_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            normalized = normalize_row(row, fields, default_usage="candidate")
            key = row_key(normalized)
            if not all(key) or key in seen:
                continue
            seen.add(key)
            existing.append(normalized)
    for row in candidates:
        key = row_key(row)
        if not all(key) or key in seen:
            continue
        seen.add(key)
        existing.append(normalize_row(row, fields, default_usage="candidate"))
    return existing


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]], output: Path, csv_path: Path, title: str, note: str) -> None:
    lines = [
        f"# {title}",
        "",
        note,
        "",
        f"- CSV: `{csv_path.relative_to(ROOT)}`",
        f"- Rows: {len(rows)}",
        "",
        "| Claim | Citekey | Source block | Read status | Evidence usage | Locator | Used in manuscript | Risk |",
        "|---|---|---|---|---|---|---:|---|",
    ]
    for row in rows[:120]:
        lines.append(
            "| {claim_id} | `{citekey}` | `{source_block_id}` | `{read_status}` | {evidence_usage_status} | {locator_status} | {used_in_manuscript} | {risk} |".format(
                **row
            )
        )
    if len(rows) > 120:
        lines.append(f"| ... | ... | ... | ... | ... | ... | {len(rows) - 120} more rows omitted |")
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build claim-evidence candidates and sync protected claim-evidence links.")
    parser.add_argument("--project", default=active_project_slug())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--candidates-output", type=Path)
    parser.add_argument("--links-output", type=Path)
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    source = args.input or project / "literature" / "evidence_locator_table.csv"
    candidates_output = args.candidates_output or project / "evidence" / "claim_evidence_candidates.csv"
    links_output = args.links_output or project / "evidence" / "claim_evidence_links.csv"
    fields = read_simple_schema(SCHEMA).get("field_order", [])
    if not isinstance(fields, list) or not fields:
        raise RuntimeError(f"Missing field_order in {SCHEMA}")
    fieldnames = [str(field) for field in fields]
    candidates = [normalize_row(row, fieldnames, default_usage="candidate") for row in build_rows(source)]
    links = sync_confirmed_links(candidates, links_output, fieldnames)
    write_csv(candidates_output, candidates, fieldnames)
    write_csv(links_output, links, fieldnames)
    write_markdown(
        candidates,
        candidates_output.with_suffix(".md"),
        candidates_output,
        "Claim-Evidence Candidates",
        "This file is generated from the evidence locator table and may be overwritten on refresh.",
    )
    write_markdown(
        links,
        links_output.with_suffix(".md"),
        links_output,
        "Protected Claim-Evidence Links",
        "This file is synced from candidates by appending new rows only. Manual evidence usage decisions are preserved.",
    )
    print(f"Wrote claim-evidence candidates: {candidates_output}")
    print(f"Synced protected claim-evidence links: {links_output}")
    print(f"Candidate rows: {len(candidates)}")
    print(f"Protected link rows: {len(links)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
