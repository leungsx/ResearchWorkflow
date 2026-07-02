#!/usr/bin/env python3
from __future__ import annotations

from workflow_config import active_project_slug


def main() -> int:
    print(active_project_slug())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
