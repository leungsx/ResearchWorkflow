#!/usr/bin/env python3
from __future__ import annotations

from rendering.collaboration import write_collaboration_state


def main() -> int:
    json_path, html_path = write_collaboration_state()
    print(f"Wrote collaboration state: {json_path}")
    print(f"Wrote collaboration page: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
