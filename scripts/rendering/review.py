from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any

from rendering.paths import REVIEW_QUEUE, REVIEW_STATE, ROOT, csv_rows
from rendering.routes import html_view_for_local_path, relative_label


def parse_date(value: str) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def note_path(value: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return None
    return path


def review_status(days_delta: int | None) -> str:
    if days_delta is None:
        return "unscheduled"
    if days_delta < 0:
        return "overdue"
    if days_delta == 0:
        return "due"
    if days_delta <= 7:
        return "upcoming_7"
    return "future"


def review_item(row: dict[str, str], today: dt.date) -> dict[str, Any]:
    due_date = parse_date(row.get("next_review", ""))
    days_delta = (due_date - today).days if due_date else None
    source = note_path(row.get("note_path", ""))
    display = html_view_for_local_path(source) if source else None
    return {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "type": row.get("type", ""),
        "stage": row.get("stage", ""),
        "next_review": due_date.isoformat() if due_date else "",
        "days_delta": days_delta,
        "status": review_status(days_delta),
        "prompt": row.get("prompt", ""),
        "source_path": relative_label(source) if source else "",
        "display_path": relative_label(display) if display else "",
    }


def build_review_state(today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.date.today()
    items = [review_item(row, today) for row in csv_rows(REVIEW_QUEUE)]
    items.sort(key=lambda item: (item["days_delta"] is None, item["days_delta"] if item["days_delta"] is not None else 9999, item["title"]))
    due_items = [item for item in items if item["days_delta"] is not None and item["days_delta"] <= 0]
    upcoming_items = [item for item in items if item["days_delta"] is not None and 0 < item["days_delta"] <= 7]
    by_type = Counter(item["type"] or "unknown" for item in items)
    by_stage = Counter(item["stage"] or "unknown" for item in items)
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "queue_path": relative_label(REVIEW_QUEUE),
        "summary": {
            "total_items": len(items),
            "due_count": len(due_items),
            "overdue_count": sum(1 for item in items if item["status"] == "overdue"),
            "upcoming_7_count": len(upcoming_items),
            "future_count": sum(1 for item in items if item["status"] == "future"),
            "unscheduled_count": sum(1 for item in items if item["status"] == "unscheduled"),
            "by_type": dict(sorted(by_type.items())),
            "by_stage": dict(sorted(by_stage.items())),
        },
        "focus_items": due_items[:12] if due_items else upcoming_items[:8],
        "due_items": due_items,
        "upcoming_7_items": upcoming_items,
        "all_items": items,
    }


def write_review_state(today: dt.date | None = None) -> Path:
    REVIEW_STATE.parent.mkdir(parents=True, exist_ok=True)
    state = build_review_state(today)
    REVIEW_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return REVIEW_STATE
