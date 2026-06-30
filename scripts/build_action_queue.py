#!/usr/bin/env python3
from __future__ import annotations

from rendering.action_queue import write_action_queue


def main() -> int:
    queue_json, queue_html = write_action_queue()
    print(f"Wrote action queue: {queue_json}")
    print(f"Wrote action queue page: {queue_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
