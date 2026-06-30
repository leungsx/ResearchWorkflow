#!/usr/bin/env python3
from __future__ import annotations

from rendering.workflow_state import write_workflow_state


def main() -> int:
    state_json, state_html = write_workflow_state()
    print(f"Wrote workflow state: {state_json}")
    print(f"Wrote workflow state page: {state_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
