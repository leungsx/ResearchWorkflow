#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "literature_matrix.schema.yaml"
MATRIX = ROOT / "library" / "literature_matrix.csv"


def read_simple_schema(path: Path = SCHEMA) -> dict[str, Any]:
    schema: dict[str, Any] = {}
    current_list: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if not raw_line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_list = None
            if value:
                schema[key] = value.strip("\"'")
            else:
                schema[key] = []
                current_list = key
            continue
        if current_list and stripped.startswith("- "):
            items = schema.setdefault(current_list, [])
            if isinstance(items, list):
                items.append(stripped[2:].strip().strip("\"'"))
    return schema


def matrix_fields(path: Path = SCHEMA) -> list[str]:
    fields = read_simple_schema(path).get("field_order", [])
    if not isinstance(fields, list) or not fields:
        raise RuntimeError(f"Missing field_order in {path}")
    return [str(field) for field in fields]


def required_fields(path: Path = SCHEMA) -> list[str]:
    fields = read_simple_schema(path).get("required_fields", [])
    return [str(field) for field in fields] if isinstance(fields, list) else []


def read_status_values(path: Path = SCHEMA) -> set[str]:
    values = read_simple_schema(path).get("read_status_values", [])
    return {str(value) for value in values} if isinstance(values, list) else set()


def path_fields(path: Path = SCHEMA) -> list[str]:
    fields = read_simple_schema(path).get("path_fields", [])
    return [str(field) for field in fields] if isinstance(fields, list) else []
