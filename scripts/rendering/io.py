from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_text_if_changed(path: Path, content: str, *, encoding: str = "utf-8") -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding=encoding, errors="ignore") == content:
        return False
    path.write_text(content, encoding=encoding)
    return True


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
