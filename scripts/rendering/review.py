from __future__ import annotations

import datetime as dt
import json
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from rendering.paths import REVIEW_QUEUE, REVIEW_STATE, ROOT, csv_rows
from rendering.routes import html_view_for_local_path, relative_label

REVIEW_BASE_FIELDS = ["id", "title", "type", "stage", "next_review", "prompt", "note_path"]
REVIEW_TRACKING_FIELDS = ["last_reviewed", "review_count", "learning_status"]
REVIEW_FIELDS = REVIEW_BASE_FIELDS + REVIEW_TRACKING_FIELDS
STAGE_INTERVAL_DAYS = {
    1: 1,
    2: 3,
    3: 7,
    4: 14,
    5: 30,
    6: 60,
}


def parse_date(value: str) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


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


def normalized_review_rows() -> list[dict[str, str]]:
    rows = csv_rows(REVIEW_QUEUE)
    normalized: list[dict[str, str]] = []
    for row in rows:
        item = {field: str(row.get(field, "") or "") for field in REVIEW_FIELDS}
        for key, value in row.items():
            if key not in item:
                item[key] = str(value or "")
        normalized.append(item)
    return normalized


def write_review_queue(rows: list[dict[str, str]]) -> None:
    REVIEW_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    extra_fields = [field for row in rows for field in row if field not in REVIEW_FIELDS]
    fieldnames = REVIEW_FIELDS + sorted(set(extra_fields))
    with REVIEW_QUEUE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def next_interval_for_stage(stage: int) -> int:
    return STAGE_INTERVAL_DAYS.get(stage, STAGE_INTERVAL_DAYS[max(STAGE_INTERVAL_DAYS)])


def mark_reviewed(
    *,
    ids: list[str] | None = None,
    all_due: bool = False,
    day: dt.date | None = None,
    next_days: int | None = None,
    learning_status: str = "learned",
) -> list[dict[str, str]]:
    day = day or dt.date.today()
    rows = normalized_review_rows()
    id_set = set(ids or [])
    if not id_set and not all_due:
        raise ValueError("必须提供 ids 或 all_due=True")

    marked: list[dict[str, str]] = []
    today = day.isoformat()
    for row in rows:
        due_date = parse_date(row.get("next_review", ""))
        selected = row.get("id", "") in id_set
        if all_due and due_date and due_date <= day:
            selected = True
        if not selected:
            continue

        current_stage = max(1, parse_int(row.get("stage", ""), default=1))
        next_stage = min(current_stage + 1, max(STAGE_INTERVAL_DAYS))
        interval = next_days if next_days is not None else next_interval_for_stage(next_stage)
        row["stage"] = str(next_stage)
        row["last_reviewed"] = today
        row["review_count"] = str(parse_int(row.get("review_count", ""), default=0) + 1)
        row["learning_status"] = learning_status
        row["next_review"] = (day + dt.timedelta(days=interval)).isoformat()
        marked.append(row.copy())

    write_review_queue(rows)
    return marked


def review_item(row: dict[str, str], today: dt.date) -> dict[str, Any]:
    due_date = parse_date(row.get("next_review", ""))
    days_delta = (due_date - today).days if due_date else None
    source = note_path(row.get("note_path", ""))
    display = html_view_for_local_path(source) if source else None
    last_reviewed = parse_date(row.get("last_reviewed", ""))
    learned_today = last_reviewed == today
    status = "learned_today" if learned_today else review_status(days_delta)
    return {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "type": row.get("type", ""),
        "stage": row.get("stage", ""),
        "next_review": due_date.isoformat() if due_date else "",
        "days_delta": days_delta,
        "status": status,
        "learning_status": row.get("learning_status", ""),
        "last_reviewed": last_reviewed.isoformat() if last_reviewed else "",
        "review_count": parse_int(row.get("review_count", ""), default=0),
        "prompt": row.get("prompt", ""),
        "source_path": relative_label(source) if source else "",
        "display_path": relative_label(display) if display else "",
    }


def build_review_state(today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.date.today()
    items = [review_item(row, today) for row in normalized_review_rows()]
    items.sort(key=lambda item: (item["days_delta"] is None, item["days_delta"] if item["days_delta"] is not None else 9999, item["title"]))
    due_items = [item for item in items if item["status"] != "learned_today" and item["days_delta"] is not None and item["days_delta"] <= 0]
    upcoming_items = [item for item in items if item["days_delta"] is not None and 0 < item["days_delta"] <= 7]
    learned_items = [item for item in items if item["status"] == "learned_today"]
    focus_candidates = [item for item in upcoming_items if item["status"] != "learned_today"]
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
            "learned_today_count": len(learned_items),
            "by_type": dict(sorted(by_type.items())),
            "by_stage": dict(sorted(by_stage.items())),
        },
        "focus_items": due_items[:12] if due_items else focus_candidates[:8],
        "due_items": due_items,
        "upcoming_7_items": upcoming_items,
        "learned_items": learned_items,
        "all_items": items,
    }


def write_review_state(today: dt.date | None = None) -> Path:
    REVIEW_STATE.parent.mkdir(parents=True, exist_ok=True)
    state = build_review_state(today)
    REVIEW_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return REVIEW_STATE
