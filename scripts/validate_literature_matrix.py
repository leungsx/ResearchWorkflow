#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from literature_matrix_schema import MATRIX, matrix_fields, path_fields, read_status_values, required_fields


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class MatrixIssue:
    status: str
    row: int
    field: str
    message: str


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def validate_matrix(path: Path = MATRIX) -> tuple[list[str], list[MatrixIssue]]:
    issues: list[MatrixIssue] = []
    expected_fields = matrix_fields()
    required = set(required_fields())
    allowed_statuses = read_status_values()
    matrix_path = path if path.is_absolute() else ROOT / path
    if not matrix_path.exists():
        return [], [MatrixIssue("FAIL", 0, "", f"matrix not found: {matrix_path}")]

    with matrix_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_fields = list(reader.fieldnames or [])
        if actual_fields != expected_fields:
            missing = [field for field in expected_fields if field not in actual_fields]
            extra = [field for field in actual_fields if field not in expected_fields]
            detail = []
            if missing:
                detail.append("missing=" + ",".join(missing))
            if extra:
                detail.append("extra=" + ",".join(extra))
            if not detail:
                detail.append("field order differs from schema")
            issues.append(MatrixIssue("FAIL", 1, "header", "; ".join(detail)))

        seen: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            citekey = (row.get("citekey") or "").strip()
            if citekey in seen:
                issues.append(MatrixIssue("FAIL", row_number, "citekey", f"duplicate citekey: {citekey}"))
            elif citekey:
                seen.add(citekey)
            for field in required:
                if not (row.get(field) or "").strip():
                    issues.append(MatrixIssue("FAIL", row_number, field, "required field is blank"))
            status = (row.get("read_status") or "").strip()
            if status and allowed_statuses and status not in allowed_statuses:
                issues.append(MatrixIssue("FAIL", row_number, "read_status", f"unknown read_status: {status}"))
            for field in path_fields():
                value = (row.get(field) or "").strip()
                if value and not resolve_path(value).exists():
                    issues.append(MatrixIssue("WARN", row_number, field, f"path does not exist: {value}"))
    return actual_fields, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate library/literature_matrix.csv against its schema.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on warnings as well as failures.")
    args = parser.parse_args()

    fields, issues = validate_matrix(args.matrix)
    failures = [issue for issue in issues if issue.status == "FAIL"]
    warnings = [issue for issue in issues if issue.status == "WARN"]
    payload = {
        "schema_version": "1.0",
        "matrix": str(args.matrix),
        "field_count": len(fields),
        "summary": {"failures": len(failures), "warnings": len(warnings)},
        "issues": [asdict(issue) for issue in issues],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif issues:
        print(f"Literature matrix validation found {len(failures)} FAIL and {len(warnings)} WARN.")
        for issue in issues[:60]:
            print(f"{issue.status}: row={issue.row} field={issue.field}: {issue.message}")
    else:
        print(f"Literature matrix validation PASS: {len(fields)} fields checked.")
    return 1 if failures or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
