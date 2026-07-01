#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rendering.review import mark_reviewed  # noqa: E402


def parse_day(value: str | None) -> dt.date | None:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mark review queue items as studied and schedule their next review.")
    parser.add_argument("--id", action="append", dest="ids", help="Review item id. Can be repeated.")
    parser.add_argument("--all-due", action="store_true", help="Mark every item due on or before --date/today as studied.")
    parser.add_argument("--date", help="Completion date in YYYY-MM-DD format; defaults to today.")
    parser.add_argument("--next-days", type=int, help="Override the spaced-review next interval in days.")
    parser.add_argument("--status", default="learned", help="learning_status value to write; default: learned.")
    args = parser.parse_args()

    if not args.ids and not args.all_due:
        parser.error("Use --id <review-id> or --all-due.")
    if args.next_days is not None and args.next_days < 1:
        parser.error("--next-days must be >= 1.")

    marked = mark_reviewed(
        ids=args.ids,
        all_due=args.all_due,
        day=parse_day(args.date),
        next_days=args.next_days,
        learning_status=args.status,
    )
    if not marked:
        print("No review items matched.")
        return 0

    print(f"Marked {len(marked)} review item(s) as studied:")
    for item in marked:
        print(f"- {item.get('id', '')}: {item.get('title', '')} -> next_review {item.get('next_review', '')} (stage {item.get('stage', '')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
