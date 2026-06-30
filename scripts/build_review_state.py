#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt

from rendering.review import write_review_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Build machine-readable review queue state.")
    parser.add_argument("--date", help="Review date in YYYY-MM-DD format; defaults to today.")
    args = parser.parse_args()
    day = dt.date.fromisoformat(args.date) if args.date else None
    output = write_review_state(day)
    print(f"Wrote review state: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
