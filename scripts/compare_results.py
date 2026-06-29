#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def compare_tables(expected: Path, actual: Path, rtol: float, atol: float) -> dict:
    left = pd.read_csv(expected)
    right = pd.read_csv(actual)
    report: dict = {
        "expected": str(expected),
        "actual": str(actual),
        "shape_expected": list(left.shape),
        "shape_actual": list(right.shape),
        "same_shape": left.shape == right.shape,
        "same_columns": list(left.columns) == list(right.columns),
        "numeric_columns_checked": [],
        "max_abs_diff": {},
        "non_numeric_mismatches": {},
        "verdict": "PASS",
    }

    if not report["same_shape"] or not report["same_columns"]:
        report["verdict"] = "FAIL"
        return report

    for column in left.columns:
        if pd.api.types.is_numeric_dtype(left[column]) and pd.api.types.is_numeric_dtype(right[column]):
            diff = (left[column] - right[column]).abs()
            max_diff = float(diff.max()) if len(diff) else 0.0
            allowed = atol + rtol * left[column].abs()
            failures = int((diff > allowed).sum())
            report["numeric_columns_checked"].append(column)
            report["max_abs_diff"][column] = max_diff
            if failures:
                report["verdict"] = "FAIL"
        else:
            mismatches = int((left[column].astype(str) != right[column].astype(str)).sum())
            report["non_numeric_mismatches"][column] = mismatches
            if mismatches:
                report["verdict"] = "FAIL"
    return report


def write_markdown(report: dict, output: Path) -> None:
    lines = [
        "# Reproducibility Comparison Report",
        "",
        f"- Expected: `{report['expected']}`",
        f"- Actual: `{report['actual']}`",
        f"- Verdict: {report['verdict']}",
        f"- Same shape: {report['same_shape']} ({report['shape_expected']} vs {report['shape_actual']})",
        f"- Same columns: {report['same_columns']}",
        "",
        "## Numeric Columns",
        "",
    ]
    for column, value in report["max_abs_diff"].items():
        lines.append(f"- `{column}` max abs diff: {value}")
    lines.extend(["", "## Non-Numeric Mismatches", ""])
    for column, value in report["non_numeric_mismatches"].items():
        lines.append(f"- `{column}` mismatches: {value}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two CSV result files for reproducibility.")
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--rtol", type=float, default=1e-5)
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = compare_tables(args.expected, args.actual, args.rtol, args.atol)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix == ".json":
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        write_markdown(report, args.output)
    print(f"Wrote comparison report: {args.output}")
    print(f"Verdict: {report['verdict']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

