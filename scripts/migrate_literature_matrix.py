#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

from literature_matrix_schema import MATRIX, matrix_fields


ROOT = Path(__file__).resolve().parents[1]


def migrate(path: Path, apply: bool) -> int:
    matrix = path if path.is_absolute() else ROOT / path
    expected = matrix_fields()
    if not matrix.exists():
        raise FileNotFoundError(matrix)
    with matrix.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = list(reader.fieldnames or [])
        rows = list(reader)
    missing = [field for field in expected if field not in actual]
    extra = [field for field in actual if field not in expected]
    order_differs = actual != expected
    print(f"Matrix: {matrix}")
    print(f"Rows: {len(rows)}")
    print(f"Missing fields: {missing or 'none'}")
    print(f"Extra fields: {extra or 'none'}")
    print(f"Field order differs: {order_differs}")
    if extra:
        print("Refusing to apply because extra fields would be dropped. Update schema first.")
        return 2
    if not apply:
        print("Dry run only. Re-run with --apply to rewrite field order and add missing fields.")
        return 0
    backup = matrix.with_suffix(matrix.suffix + f".bak-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}")
    backup.write_text(matrix.read_text(encoding="utf-8-sig"), encoding="utf-8")
    with matrix.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=expected, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in expected})
    print(f"Wrote migrated matrix: {matrix}")
    print(f"Backup: {backup}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Add missing literature matrix fields and restore schema field order.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return migrate(args.matrix, apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
