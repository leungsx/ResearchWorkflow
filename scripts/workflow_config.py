#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only when PyYAML is not installed.
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "workflow.yaml"


def _clean(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _scalar(value: str) -> str:
    return _clean(value)


def _fallback_parse(path: Path) -> dict[str, object]:
    config: dict[str, object] = {}
    lines = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if line.strip():
            lines.append(line)

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(" ") or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        index += 1
        if value:
            config[key] = _scalar(value)
            continue
        children: list[str] = []
        while index < len(lines) and lines[index].startswith("  "):
            children.append(lines[index])
            index += 1
        if children and children[0].strip().startswith("- "):
            items: list[object] = []
            child_index = 0
            while child_index < len(children):
                child = children[child_index]
                stripped = child.strip()
                if not stripped.startswith("- "):
                    child_index += 1
                    continue
                item = stripped[2:].strip()
                if ":" not in item:
                    items.append(_scalar(item))
                    child_index += 1
                    continue
                item_key, item_value = item.split(":", 1)
                row: dict[str, str] = {item_key.strip(): _scalar(item_value)}
                child_index += 1
                while child_index < len(children) and children[child_index].startswith("    "):
                    nested = children[child_index].strip()
                    if ":" in nested:
                        nested_key, nested_value = nested.split(":", 1)
                        row[nested_key.strip()] = _scalar(nested_value)
                    child_index += 1
                items.append(row)
            config[key] = items
            continue
        mapping: dict[str, object] = {}
        child_index = 0
        while child_index < len(children):
            child = children[child_index]
            if not child.startswith("  ") or child.startswith("    ") or ":" not in child:
                child_index += 1
                continue
            child_key, child_value = child.strip().split(":", 1)
            child_key = child_key.strip()
            child_value = child_value.strip()
            child_index += 1
            if child_value:
                mapping[child_key] = _scalar(child_value)
                continue
            nested_map: dict[str, str] = {}
            while child_index < len(children) and children[child_index].startswith("    "):
                nested = children[child_index].strip()
                if ":" in nested:
                    nested_key, nested_value = nested.split(":", 1)
                    nested_map[nested_key.strip()] = _scalar(nested_value)
                child_index += 1
            mapping[child_key] = nested_map
        config[key] = mapping
    return config


def read_workflow_config(path: Path = CONFIG) -> dict[str, object]:
    if not path.exists():
        return {}
    if yaml is not None:
        payload: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return payload if isinstance(payload, dict) else {}
    return _fallback_parse(path)


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
