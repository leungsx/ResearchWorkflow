#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"

BLOCKED_READ_STATUSES = {"", "metadata-only", "abstract-only", "ai-summarized", "unread"}
ACCEPTED_READ_STATUSES = {"human-read", "verified"}
PARTIAL_READ_STATUSES = {"skimmed"}
CRITICAL_USAGE_STATUSES = {"claim-linked", "manuscript-cited", "submission-evidence"}


@dataclass
class EvidenceIssue:
    severity: str
    location: str
    issue: str
    suggestion: str


def load_matrix(matrix: Path = MATRIX) -> list[dict[str, str]]:
    if not matrix.exists():
        return []
    with matrix.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def project_has_tag(row: dict[str, str], project: Path) -> bool:
    tags = row.get("project_tags", "")
    return bool(tags and project.name in tags)


def reader_path(project: Path, citekey: str) -> Path:
    return project / "literature" / "readers" / citekey / "paper.md"


def has_source_locator(project: Path, row: dict[str, str]) -> bool:
    citekey = row.get("citekey", "")
    paths = [row.get("pdf_path", ""), row.get("note_path", "")]
    if citekey and reader_path(project, citekey).exists():
        return True
    for raw_path in paths:
        if not raw_path.strip():
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            return True
    return False


def material_files(project: Path) -> list[tuple[str, Path, bool]]:
    return [
        ("claim-evidence map", project / "07_claim_evidence_map.md", True),
        ("manuscript", project / "manuscript" / "paper.md", True),
        ("literature synthesis", project / "03_literature_synthesis.md", False),
        ("references", project / "manuscript" / "references.bib", False),
    ]


def claim_evidence_links(project: Path) -> Path:
    return project / "evidence" / "claim_evidence_links.csv"


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "是"}


def critical_usage(row: dict[str, str]) -> bool:
    usage = row.get("evidence_usage_status", "").strip()
    return usage in CRITICAL_USAGE_STATUSES or truthy(row.get("used_in_manuscript", ""))


def structured_citekey_usages(project: Path, citekey: str) -> list[tuple[str, Path, bool]]:
    path = claim_evidence_links(project)
    if not citekey or not path.exists():
        return []
    usages: list[tuple[str, Path, bool]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("citekey", "").strip() != citekey:
                continue
            critical = critical_usage(row)
            label = "structured claim-evidence link"
            if row.get("claim_id"):
                label += f" {row['claim_id']}"
            if row.get("evidence_usage_status"):
                label += f" [{row['evidence_usage_status']}]"
            usages.append((label, path, critical))
    return usages


def citekey_usages(project: Path, citekey: str) -> list[tuple[str, Path, bool]]:
    usages = []
    if not citekey:
        return usages
    for label, path, critical in material_files(project):
        if citekey in read_text(path):
            usages.append((label, path, critical))
    usages.extend(structured_citekey_usages(project, citekey))
    return usages


def audit_project(project: Path, matrix: Path = MATRIX) -> tuple[str, list[EvidenceIssue]]:
    rows = load_matrix(matrix)
    issues: list[EvidenceIssue] = []
    used_count = 0
    project_tagged = 0

    for row in rows:
        citekey = row.get("citekey", "").strip()
        if not citekey:
            continue
        usages = citekey_usages(project, citekey)
        tagged = project_has_tag(row, project)
        if usages:
            used_count += 1
        if tagged:
            project_tagged += 1
        if not usages and not tagged:
            continue

        status = (row.get("read_status", "") or "").strip()
        source_locator = has_source_locator(project, row)
        critical_usages = [item for item in usages if item[2]]
        all_usage_labels = ", ".join(item[0] for item in usages) or "project literature pool"
        location = f"{citekey} ({all_usage_labels})"

        if critical_usages and status in BLOCKED_READ_STATUSES:
            issues.append(
                EvidenceIssue(
                    "ERROR",
                    location,
                    f"Used as manuscript/claim evidence but read_status is `{status or 'blank'}`.",
                    "Obtain the legal full text, create a source-grounded reader or note, then mark the source `human-read` or `verified` before using it as evidence.",
                )
            )
            continue

        if critical_usages and status in PARTIAL_READ_STATUSES:
            issues.append(
                EvidenceIssue(
                    "WARN",
                    location,
                    "Used in a critical writing file but only marked `skimmed`.",
                    "Upgrade to `human-read` or `verified` before treating this source as manuscript evidence.",
                )
            )

        if critical_usages and status in ACCEPTED_READ_STATUSES and not source_locator:
            issues.append(
                EvidenceIssue(
                    "ERROR",
                    location,
                    f"Read status is `{status}` but no source locator was found.",
                    "Add `pdf_path`, `note_path`, or a reader package under `literature/readers/<citekey>/`.",
                )
            )

        if not critical_usages and usages and status in BLOCKED_READ_STATUSES:
            issues.append(
                EvidenceIssue(
                    "WARN",
                    location,
                    f"Referenced in project materials but still `{status or 'blank'}`.",
                    "Keep it out of manuscript claims until full-text reading and source locators are available.",
                )
            )
        elif not usages and tagged and status in BLOCKED_READ_STATUSES:
            issues.append(
                EvidenceIssue(
                    "INFO",
                    location,
                    f"Project-tagged source remains `{status or 'blank'}`.",
                    "This is acceptable for a frontier pool, but not for manuscript evidence.",
                )
            )

        if not critical_usages and tagged and row.get("pdf_path", "").strip() and status in BLOCKED_READ_STATUSES:
            issues.append(
                EvidenceIssue(
                    "WARN",
                    location,
                    "PDF path exists but read_status was not upgraded.",
                    "If the full text was actually read, update `read_status` and add a source-grounded note or reader.",
                )
            )

    report = render_report(project, matrix, rows, issues, used_count, project_tagged)
    return report, issues


def summarize(issues: list[EvidenceIssue]) -> dict[str, int | str]:
    counts = {
        "ERROR": sum(1 for issue in issues if issue.severity == "ERROR"),
        "WARN": sum(1 for issue in issues if issue.severity == "WARN"),
        "INFO": sum(1 for issue in issues if issue.severity == "INFO"),
    }
    if counts["ERROR"]:
        status = "NEEDS_FIX"
    elif counts["WARN"]:
        status = "WARNINGS"
    else:
        status = "PASS"
    return {"status": status, **counts}


def render_report(
    project: Path,
    matrix: Path,
    rows: list[dict[str, str]],
    issues: list[EvidenceIssue],
    used_count: int,
    project_tagged: int,
) -> str:
    summary = summarize(issues)
    lines = [
        "# Evidence Gate Report",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Project: `{project.name}`",
        f"Matrix: `{matrix}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Status | {summary['status']} |",
        f"| Literature matrix rows | {len(rows)} |",
        f"| Project-tagged rows | {project_tagged} |",
        f"| Citekeys used in project materials | {used_count} |",
        f"| ERROR issues | {summary['ERROR']} |",
        f"| WARN issues | {summary['WARN']} |",
        f"| INFO issues | {summary['INFO']} |",
        "",
        "## Gate Rules",
        "",
        "- `metadata-only`, `abstract-only`, `ai-summarized`, `unread`, or blank sources cannot support manuscript claims.",
        "- Critical manuscript evidence should be `human-read` or `verified`.",
        "- Accepted evidence needs a source locator: `pdf_path`, `note_path`, or `literature/readers/<citekey>/paper.md`.",
        "",
        "## Issues",
        "",
    ]
    if issues:
        lines.extend(["| Severity | Location | Issue | Suggested action |", "|---|---|---|---|"])
        for issue in issues:
            lines.append(f"| {issue.severity} | `{issue.location}` | {issue.issue} | {issue.suggestion} |")
    else:
        lines.append("- No evidence gate issues detected.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit whether project evidence is safe for manuscript use.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="Project slug under projects/")
    group.add_argument("--project-path", type=Path, help="Arbitrary project path")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--output", type=Path, help="Defaults to manuscript/evidence_gate_report.md for project slugs")
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--fail-on-errors", action="store_true")
    args = parser.parse_args()

    project = PROJECTS / args.project if args.project else args.project_path
    if project is None or not project.exists():
        raise FileNotFoundError(project)

    report, issues = audit_project(project, args.matrix)
    output = args.output
    if output is None and args.project:
        output = project / "manuscript" / "evidence_gate_report.md"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Wrote evidence gate report: {output}")
    if args.stdout or not output:
        print(report)
    if args.fail_on_errors and any(issue.severity == "ERROR" for issue in issues):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
