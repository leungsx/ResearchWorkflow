#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "workflow.yaml"


def _clean(value: str) -> str:
    return value.strip().strip('"').strip("'")


def read_workflow_config(path: Path = CONFIG) -> dict[str, object]:
    config: dict[str, object] = {}
    if not path.exists():
        return config

    current_list: str | None = None
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list:
            items = config.setdefault(current_list, [])
            if isinstance(items, list):
                items.append(_clean(line[4:]))
            continue
        if not raw_line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_list = None
            if value:
                config[key] = _clean(value)
            else:
                config[key] = []
                current_list = key
    return config


def active_project_slug(default: str = "library_short_video") -> str:
    value = read_workflow_config().get("active_project")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def dashboard_project_slugs() -> list[str]:
    config = read_workflow_config()
    value = config.get("dashboard_projects")
    if isinstance(value, list):
        projects = [str(item).strip() for item in value if str(item).strip()]
        if projects:
            return projects
    return [active_project_slug()]
