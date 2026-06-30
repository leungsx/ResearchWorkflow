#!/usr/bin/env python3
from __future__ import annotations

from rendering.search import write_search_index


def main() -> int:
    output = write_search_index()
    print(f"Wrote search index: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
