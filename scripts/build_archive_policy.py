#!/usr/bin/env python3
from __future__ import annotations

from rendering.archive_policy import write_archive_policy


def main() -> int:
    json_path, html_path = write_archive_policy()
    print(f"Wrote archive policy: {json_path}")
    print(f"Wrote archive policy page: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
