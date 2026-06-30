#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from rendering.schemas import validate_workflow_schemas


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ResearchWorkflow machine-state schemas.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation report.")
    args = parser.parse_args()

    report = validate_workflow_schemas()
    failures = [issue for issue in report.issues if issue.status == "FAIL"]
    warnings = [issue for issue in report.issues if issue.status == "WARN"]
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "checked_files": report.checked_files,
                    "summary": {
                        "checked_file_count": len(report.checked_files),
                        "failures": len(failures),
                        "warnings": len(warnings),
                    },
                    "issues": [issue.__dict__ for issue in report.issues],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if not report.issues:
            print(f"Schema validation PASS: {len(report.checked_files)} files checked.")
        else:
            print(f"Schema validation found {len(failures)} FAIL and {len(warnings)} WARN across {len(report.checked_files)} files.")
            for issue in report.issues[:40]:
                print(f"{issue.status}: {issue.path}: {issue.message}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
