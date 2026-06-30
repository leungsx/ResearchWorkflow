from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from rendering.manifest import artifact_manifest_rows
from rendering.paths import ROOT, SEARCH_INDEX_JSON, read_text


INDEXABLE_SUFFIXES = {".md", ".html", ".csv", ".json", ".yaml", ".yml", ".txt"}


def clean_text(value: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    value = re.sub(r"(?m)^---\s*$.*?^---\s*$", " ", value, count=1, flags=re.S)
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[\[\]#*_`>|{}]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def source_text(path: Path) -> str:
    if path.is_dir():
        children = sorted(item.name for item in path.iterdir() if not item.name.startswith("."))
        return " ".join(children[:80])
    if not path.exists() or path.suffix not in INDEXABLE_SUFFIXES:
        return ""
    return clean_text(read_text(path, limit=24000))


def summary_for(text: str, limit: int = 260) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def entry_id(row: dict[str, str]) -> str:
    key = f"{row.get('source_path', '')}|{row.get('display_path', '')}|{row.get('display_type', '')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def build_search_index(rows: list[dict[str, str]] | None = None) -> dict[str, Any]:
    rows = rows if rows is not None else artifact_manifest_rows()
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        display_path = row.get("display_path", "")
        if not display_path or not display_path.endswith(".html"):
            continue
        source = ROOT / row.get("source_path", "")
        display = ROOT / display_path
        if not display.exists():
            continue
        text = source_text(source)
        title = row.get("title", "") or source.name
        searchable = clean_text(
            " ".join(
                [
                    title,
                    row.get("source_path", ""),
                    row.get("display_path", ""),
                    row.get("display_type", ""),
                    row.get("layer", ""),
                    text,
                ]
            )
        )
        item = {
            "id": entry_id(row),
            "title": title,
            "layer": row.get("layer", ""),
            "display_type": row.get("display_type", ""),
            "source_type": row.get("source_type", ""),
            "source_path": row.get("source_path", ""),
            "display_path": display_path,
            "summary": summary_for(text),
            "search_text": searchable.lower(),
        }
        dedupe_key = f"{item['display_path']}|{item['title']}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        entries.append(item)

    entries.sort(key=lambda item: (item["layer"], item["display_type"], item["title"]))
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "entry_count": len(entries),
        "entries": entries,
    }


def write_search_index(rows: list[dict[str, str]] | None = None) -> Path:
    SEARCH_INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = build_search_index(rows)
    SEARCH_INDEX_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return SEARCH_INDEX_JSON
