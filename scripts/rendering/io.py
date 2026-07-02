from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

GENERATED_AT_RE = re.compile(r"(Generated:?\s+)\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def write_text_if_changed(path: Path, content: str, *, encoding: str = "utf-8") -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding=encoding, errors="ignore") == content:
        return False
    path.write_text(content, encoding=encoding)
    return True


def write_text_preserving_generated_at(path: Path, content: str, *, encoding: str = "utf-8") -> bool:
    if path.exists():
        previous = path.read_text(encoding=encoding, errors="ignore")
        if GENERATED_AT_RE.sub(r"\1TIMESTAMP", previous) == GENERATED_AT_RE.sub(r"\1TIMESTAMP", content):
            content = previous
    return write_text_if_changed(path, content, encoding=encoding)


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
        comparable_previous = dict(previous) if isinstance(previous, dict) else {}
        comparable_payload = dict(payload)
        comparable_previous.pop("generated_at", None)
        comparable_payload.pop("generated_at", None)
        if comparable_previous == comparable_payload and isinstance(previous.get("generated_at"), str):
            payload["generated_at"] = previous["generated_at"]
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
