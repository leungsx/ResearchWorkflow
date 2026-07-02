#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCLUDE_PARTS = {".git", "__pycache__", "backups", "library/pdfs", "tools/caj2pdf"}
TEXT_SUFFIXES = {".bib", ".csv", ".html", ".json", ".md", ".py", ".txt", ".yaml", ".yml", ".toml", ".tsv"}

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|cookie|password|passwd)\b\s*[:=]\s*[\"']?[A-Za-z0-9_./+=:-]{12,}"),
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9_./+=:-]{20,}"),
    re.compile(r"密码\s*[:：=]\s*\S{6,}"),
]
WARNING_PATTERNS = [
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(身份证|受试者|访谈记录|原始评论|内部资料|未发表|投稿中|审稿意见)", re.IGNORECASE),
]


@dataclass
class PrivacyIssue:
    status: str
    path: str
    line: int
    pattern: str
    snippet: str


def git_tracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return [path for path in ROOT.rglob("*") if path.is_file()]
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def is_excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if any(part in path.parts for part in {".git", "__pycache__"}):
        return True
    return any(rel == part or rel.startswith(part + "/") for part in DEFAULT_EXCLUDE_PARTS)


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES and not is_excluded(path)


def scan_path(path: Path) -> list[PrivacyIssue]:
    issues: list[PrivacyIssue] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return issues
    rel = path.relative_to(ROOT).as_posix()
    for line_number, line in enumerate(text.splitlines(), start=1):
        clean = line.strip()
        if not clean:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(clean):
                issues.append(PrivacyIssue("FAIL", rel, line_number, pattern.pattern, clean[:180]))
        for pattern in WARNING_PATTERNS:
            if pattern.search(clean):
                issues.append(PrivacyIssue("WARN", rel, line_number, pattern.pattern, clean[:180]))
                break
    return issues


def audit_paths(paths: list[Path] | None = None) -> list[PrivacyIssue]:
    candidates = paths or git_tracked_paths()
    issues: list[PrivacyIssue] = []
    for path in candidates:
        if path.exists() and path.is_file() and is_text_candidate(path):
            issues.extend(scan_path(path))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked text files for sensitive research or secret material.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings are present.")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    issues = audit_paths()
    failures = [issue for issue in issues if issue.status == "FAIL"]
    warnings = [issue for issue in issues if issue.status == "WARN"]
    payload = {
        "schema_version": "1.0",
        "summary": {"failures": len(failures), "warnings": len(warnings), "issue_count": len(issues)},
        "issues": [asdict(issue) for issue in issues],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Privacy audit: FAIL={len(failures)} WARN={len(warnings)}")
        for issue in issues[: args.limit]:
            print(f"{issue.status}: {issue.path}:{issue.line}: {issue.snippet}")
        if len(issues) > args.limit:
            print(f"... {len(issues) - args.limit} more issues omitted")
    return 1 if failures or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
