#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

import evidence_gate


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LATIN_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z-]{2,}\b")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s。；;，,]+", re.IGNORECASE)
NUMBERED_CITATION_RE = re.compile(r"[\[［]([0-9０-９,\-–—，、;；\s]+)[\]］]")
REF_HEADING_RE = re.compile(r"^#{1,6}\s*(References|参考文献)\s*$", re.IGNORECASE)
REF_NUMBER_RE = re.compile(r"^\s*(?:[\[［](\d+)[\]］]|(\d+)[\.\、])\s*(.+)$")
DOC_TYPE_RE = re.compile(r"\[(J|M|C|D|R|N|P|S|Z|EB/OL|DB/OL|CP/OL)\]", re.IGNORECASE)


@dataclass
class Issue:
    severity: str
    location: str
    issue: str
    suggestion: str


@dataclass
class ReferenceEntry:
    label: str
    text: str
    source: str
    number: int | None = None


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def has_english_translation(text: str) -> bool:
    if not has_cjk(text):
        return True
    cleaned = re.sub(r"https?://\S+|doi\s*:?\s*\S+|10\.\d{4,9}/\S+", " ", text, flags=re.IGNORECASE)
    words = LATIN_WORD_RE.findall(cleaned)
    meaningful_words = [
        word
        for word in words
        if word.lower() not in {"doi", "http", "https", "www", "cn", "com", "org", "net", "eb", "ol"}
    ]
    if len(meaningful_words) >= 4:
        return True
    translation_markers = ("英文", "English", "translation", "in Chinese", "Translated", "译")
    return any(marker.lower() in text.lower() for marker in translation_markers)


def normalize_digits(text: str) -> str:
    table = str.maketrans("０１２３４５６７８９", "0123456789")
    return text.translate(table)


def expand_citation_token(token: str) -> set[int]:
    token = normalize_digits(token)
    token = token.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",")
    token = token.replace("–", "-").replace("—", "-")
    numbers: set[int] = set()
    for part in token.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_raw, end_raw = part.split("-", 1)
            if start_raw.strip().isdigit() and end_raw.strip().isdigit():
                start = int(start_raw)
                end = int(end_raw)
                if 0 < start <= end <= 1000:
                    numbers.update(range(start, end + 1))
                continue
        if part.isdigit():
            numbers.add(int(part))
    return numbers


def extract_in_text_numbers(text: str) -> set[int]:
    numbers: set[int] = set()
    body = text
    ref_start = find_reference_start(text)
    if ref_start is not None:
        body = text[:ref_start]
    for match in NUMBERED_CITATION_RE.finditer(body):
        numbers.update(expand_citation_token(match.group(1)))
    return numbers


def find_reference_start(text: str) -> int | None:
    offset = 0
    for line in text.splitlines(keepends=True):
        if REF_HEADING_RE.match(line.strip()):
            return offset
        offset += len(line)
    return None


def extract_markdown_references(text: str) -> list[ReferenceEntry]:
    lines = text.splitlines()
    start_index: int | None = None
    for idx, line in enumerate(lines):
        if REF_HEADING_RE.match(line.strip()):
            start_index = idx + 1
    if start_index is None:
        return []

    entries: list[ReferenceEntry] = []
    current_number: int | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_text
        if current_number is None or not current_text:
            current_number = None
            current_text = []
            return
        entries.append(
            ReferenceEntry(
                label=str(current_number),
                number=current_number,
                text=" ".join(part.strip() for part in current_text if part.strip()),
                source="paper.md",
            )
        )
        current_number = None
        current_text = []

    for line in lines[start_index:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            break
        match = REF_NUMBER_RE.match(stripped)
        if match:
            flush()
            current_number = int(match.group(1) or match.group(2))
            current_text = [match.group(3)]
            continue
        if current_number is not None:
            current_text.append(stripped)
    flush()
    return entries


def parse_bibtex_entries(path: Path) -> list[ReferenceEntry]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries: list[ReferenceEntry] = []
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@|\Z)", text, re.DOTALL):
        entry_type, key, body = match.groups()
        flattened = " ".join(line.strip() for line in body.splitlines() if line.strip())
        entries.append(ReferenceEntry(label=key.strip(), text=f"@{entry_type}{{{key}, {flattened}", source=path.name))
    return entries


def detect_reference_issues(entry: ReferenceEntry) -> list[Issue]:
    issues: list[Issue] = []
    loc = f"{entry.source}:{entry.label}"
    text = entry.text

    if entry.source == "paper.md" and entry.number is None:
        issues.append(Issue("ERROR", loc, "参考文献未使用顺序编码。", "按 GB/T 7714-2015 使用 [1]、[2] 等顺序编码。"))

    if not re.search(r"\b(19|20)\d{2}\b", text):
        issues.append(Issue("ERROR", loc, "未检测到出版年份。", "补齐出版年，并核对与正文引用一致。"))

    if entry.source == "paper.md" and not DOC_TYPE_RE.search(text):
        issues.append(Issue("WARN", loc, "未检测到文献类型标识。", "为期刊、专著、会议、学位论文、网页等补充 [J]、[M]、[C]、[D]、[EB/OL] 等标识。"))

    if has_cjk(text) and not has_english_translation(text):
        issues.append(
            Issue(
                "ERROR",
                loc,
                "中文参考文献缺少英文翻译信息。",
                "按《图书情报工作》要求，为中文文献补充英文题名、刊名/出版信息等英译信息。",
            )
        )

    author_segment = text.split(".", 1)[0].split("．", 1)[0]
    if has_cjk(author_segment):
        separators = author_segment.count(",") + author_segment.count("，") + author_segment.count("、")
        if separators >= 3 and "等" not in author_segment and "et al" not in author_segment.lower():
            issues.append(Issue("WARN", loc, "疑似列出超过 3 位作者但未使用“等”。", "超过 3 位作者时，通常著录前 3 位后加“等”或 et al.。"))

    for doi in DOI_RE.findall(text):
        if doi.endswith((".", "。", ",", "，", ";", "；")):
            issues.append(Issue("WARN", loc, "DOI 后带有句末标点。", "移除 DOI/URL 后的句号或逗号，避免链接失效。"))
    if re.search(r"\bdx\.doi\.org\b", text, re.IGNORECASE):
        issues.append(Issue("WARN", loc, "DOI 使用了旧式 dx.doi.org 域名。", "改为 https://doi.org/10.xxxx。"))
    if re.search(r"\bdoi\s*:\s*10\.", text, re.IGNORECASE):
        issues.append(Issue("INFO", loc, "DOI 使用 doi: 前缀。", "投稿前统一为期刊接受的 DOI 写法；如需 URL 形式，用 https://doi.org/10.xxxx。"))

    if entry.source.endswith(".bib"):
        lowered = text.lower()
        for field in ("author", "title", "year"):
            if f"{field}" not in lowered:
                issues.append(Issue("ERROR", loc, f"BibTeX 条目缺少 {field} 字段。", f"补齐 {field} 字段后再导出参考文献。"))
        if has_cjk(text) and not any(token in lowered for token in ("title_en", "journal_en", "english", "translation")):
            issues.append(
                Issue(
                    "ERROR",
                    loc,
                    "中文 BibTeX 条目未检测到英文翻译字段。",
                    "增加 title_en、journal_en、note 或 translation 字段，保留投稿所需英译信息。",
                )
            )

    return issues


def audit(project: Path | None, paper: Path | None, references: Path | None) -> tuple[str, list[Issue]]:
    if project:
        paper = project / "manuscript" / "paper.md"
        references = project / "manuscript" / "references.bib"
    if paper is None:
        raise ValueError("Either --project or --paper is required.")

    issues: list[Issue] = []
    paper_text = paper.read_text(encoding="utf-8", errors="ignore") if paper.exists() else ""
    if not paper.exists():
        issues.append(Issue("ERROR", str(paper), "未找到论文正文。", "先创建或 backfill `manuscript/paper.md`。"))

    in_text_numbers = extract_in_text_numbers(paper_text)
    markdown_refs = extract_markdown_references(paper_text)
    bib_refs = parse_bibtex_entries(references) if references else []
    all_refs = markdown_refs + bib_refs

    markdown_numbers = {entry.number for entry in markdown_refs if entry.number is not None}
    if in_text_numbers and markdown_numbers:
        missing_refs = sorted(number for number in in_text_numbers if number not in markdown_numbers)
        orphan_refs = sorted(number for number in markdown_numbers if number not in in_text_numbers)
        for number in missing_refs:
            issues.append(Issue("ERROR", f"正文引用[{number}]", "正文引用没有对应参考文献。", "补齐参考文献条目，或删除/替换该引用。"))
        for number in orphan_refs:
            issues.append(Issue("WARN", f"参考文献[{number}]", "参考文献未在正文中检测到引用。", "确认是否需要引用；不需要则删除。"))
    elif markdown_refs and not in_text_numbers:
        issues.append(Issue("WARN", str(paper), "有参考文献但未检测到正文顺序编码引用。", "在正文按出现顺序加入 [1]、[2] 等引用标记。"))
    elif in_text_numbers and not markdown_refs:
        issues.append(Issue("ERROR", str(paper), "正文有顺序编码引用但参考文献列表为空。", "在 `# References` 或 `# 参考文献` 后补齐编号条目。"))

    if not all_refs:
        issues.append(Issue("WARN", str(paper), "未检测到参考文献条目。", "写作阶段可以为空；投稿前必须补齐并运行本审计。"))

    for entry in all_refs:
        issues.extend(detect_reference_issues(entry))

    evidence_summary = None
    if project:
        _evidence_report, evidence_issues = evidence_gate.audit_project(project)
        evidence_summary = evidence_gate.summarize(evidence_issues)
        for evidence_issue in evidence_issues:
            if evidence_issue.severity in {"ERROR", "WARN"}:
                issues.append(
                    Issue(
                        evidence_issue.severity,
                        evidence_issue.location,
                        "证据门禁：" + evidence_issue.issue,
                        evidence_issue.suggestion,
                    )
                )

    report = render_report(project, paper, references, in_text_numbers, markdown_refs, bib_refs, issues, evidence_summary)
    return report, issues


def render_issue_table(issues: list[Issue]) -> list[str]:
    if not issues:
        return ["- No issues detected by the heuristic checker."]
    lines = ["| Severity | Location | Issue | Suggested action |", "|---|---|---|---|"]
    for issue in issues:
        lines.append(f"| {issue.severity} | `{issue.location}` | {issue.issue} | {issue.suggestion} |")
    return lines


def render_report(
    project: Path | None,
    paper: Path,
    references: Path | None,
    in_text_numbers: set[int],
    markdown_refs: list[ReferenceEntry],
    bib_refs: list[ReferenceEntry],
    issues: list[Issue],
    evidence_summary: dict[str, int | str] | None = None,
) -> str:
    error_count = sum(1 for issue in issues if issue.severity == "ERROR")
    warn_count = sum(1 for issue in issues if issue.severity == "WARN")
    info_count = sum(1 for issue in issues if issue.severity == "INFO")
    status = "PASS" if error_count == 0 else "NEEDS_FIX"

    lines = [
        "# GB/T 7714 And Chinese Reference Audit",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Project: `{project.name if project else ''}`",
        f"Paper: `{paper}`",
        f"References: `{references}`" if references else "References: not provided",
        "",
        "This is a deterministic heuristic audit. It catches common problems before submission, but it does not replace manual journal proofing.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Status | {status} |",
        f"| Numbered in-text citation labels | {len(in_text_numbers)} |",
        f"| Markdown reference entries | {len(markdown_refs)} |",
        f"| BibTeX entries | {len(bib_refs)} |",
        f"| ERROR issues | {error_count} |",
        f"| WARN issues | {warn_count} |",
        f"| INFO issues | {info_count} |",
    ]
    if evidence_summary:
        lines.extend(
            [
                f"| Evidence gate status | {evidence_summary['status']} |",
                f"| Evidence gate ERROR issues | {evidence_summary['ERROR']} |",
                f"| Evidence gate WARN issues | {evidence_summary['WARN']} |",
            ]
        )
    lines.extend(["", "## Issues", ""])
    lines.extend(render_issue_table(issues))
    lines.extend(
        [
            "",
            "## What This Checks",
            "",
            "- GB/T 7714-style sequential citation consistency.",
            "- Missing publication years and document type markers such as `[J]`, `[M]`, `[D]`, `[EB/OL]`.",
            "- Chinese references that appear to lack English translation information.",
            "- Overlong Chinese author lists that may need `等`.",
            "- DOI/URL hygiene issues.",
            "- Evidence-state problems for cited or claim-linked sources when a project is provided.",
            "",
            "## Manual Checks Still Required",
            "",
            "- Whether each cited source actually supports the local claim.",
            "- Whether every Chinese reference's English translation matches the official title/source.",
            "- Whether final punctuation, capitalization, and spacing match the latest journal template.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit references for 《图书情报工作》 / GB/T 7714 readiness.")
    parser.add_argument("--project", help="Project slug under projects/")
    parser.add_argument("--paper", type=Path, help="Path to manuscript markdown")
    parser.add_argument("--references", type=Path, help="Path to references.bib")
    parser.add_argument("--output", type=Path, help="Output report path")
    parser.add_argument("--stdout", action="store_true", help="Print report to stdout")
    parser.add_argument("--fail-on-errors", action="store_true", help="Exit 2 when ERROR issues are found")
    args = parser.parse_args()

    project = PROJECTS / args.project if args.project else None
    if project and not project.exists():
        raise FileNotFoundError(project)
    report, issues = audit(project, args.paper, args.references)

    output = args.output
    if output is None and project:
        output = project / "manuscript" / "citation_audit_gbt7714.md"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Wrote citation audit: {output}")
    if args.stdout or not output:
        print(report)

    if args.fail_on_errors and any(issue.severity == "ERROR" for issue in issues):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
