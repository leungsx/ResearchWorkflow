from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from workflow_config import active_project_slug
from rendering.manifest import artifact_manifest_rows
from rendering.paths import ROOT, SEARCH_INDEX_JSON, read_text


INDEXABLE_SUFFIXES = {".md", ".html", ".csv", ".json", ".yaml", ".yml", ".txt"}
TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}")
STOPWORDS = {
    "html",
    "json",
    "markdown",
    "source",
    "display",
    "generated",
    "project",
    "paper",
    "view",
    "index",
}
TYPE_WEIGHTS = {
    "paper_today_entry": 130,
    "paper_page": 120,
    "concept_card_view": 110,
    "method_card_view": 110,
    "project_state": 105,
    "workflow_state": 100,
    "action_queue": 100,
    "review_today": 95,
    "knowledge_graph": 90,
    "search": 85,
    "markdown_view": 75,
    "directory_view": 45,
}
SEARCH_TEXT_LIMIT = 3000


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


def snippet_for(text: str, limit: int = 1800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def tokens_for(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def keywords_for(title: str, source_path: str, display_type: str, layer: str, text: str) -> list[str]:
    weighted = " ".join([title, title, source_path, display_type, layer, text[:4000]])
    counter = Counter(token for token in tokens_for(weighted) if token not in STOPWORDS and len(token) <= 32)
    return [token for token, _ in counter.most_common(12)]


def date_for(*values: str) -> str:
    joined = " ".join(values)
    match = re.search(r"\b(20\d{2})[-_/]?(0[1-9]|1[0-2])[-_/]?([0-3]\d)\b", joined)
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def project_for(source_path: str, display_path: str) -> str:
    active_project = active_project_slug()
    for value in [source_path, display_path]:
        parts = Path(value).parts
        if "projects" in parts:
            index = parts.index("projects")
            if index + 1 < len(parts):
                return parts[index + 1]
        if active_project and active_project in value:
            return active_project
    return ""


def weight_for(display_type: str, layer: str, title: str) -> int:
    weight = TYPE_WEIGHTS.get(display_type, 60)
    if layer == "Knowledge":
        weight += 8
    elif layer == "Presentation":
        weight += 5
    if "入口" in title or "状态" in title:
        weight += 5
    return weight


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
        source_path = row.get("source_path", "")
        display_type = row.get("display_type", "")
        layer = row.get("layer", "")
        display_date = date_for(source_path, display_path, title)
        project = project_for(source_path, display_path)
        keywords = keywords_for(title, source_path, display_type, layer, text)
        search_body = text[:SEARCH_TEXT_LIMIT]
        searchable = clean_text(
            " ".join(
                [
                    title,
                    source_path,
                    display_path,
                    display_type,
                    layer,
                    display_date,
                    project,
                    " ".join(keywords),
                    search_body,
                ]
            )
        )
        item = {
            "id": entry_id(row),
            "title": title,
            "layer": layer,
            "display_type": display_type,
            "source_type": row.get("source_type", ""),
            "source_path": source_path,
            "display_path": display_path,
            "summary": summary_for(text),
            "snippet_text": snippet_for(text),
            "keywords": keywords,
            "date": display_date,
            "project": project,
            "weight": weight_for(display_type, layer, title),
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
    if SEARCH_INDEX_JSON.exists():
        try:
            previous = json.loads(SEARCH_INDEX_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
        comparable_previous = dict(previous)
        comparable_payload = dict(payload)
        comparable_previous.pop("generated_at", None)
        comparable_payload.pop("generated_at", None)
        if comparable_previous == comparable_payload and isinstance(previous.get("generated_at"), str):
            payload["generated_at"] = previous["generated_at"]
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if SEARCH_INDEX_JSON.exists() and SEARCH_INDEX_JSON.read_text(encoding="utf-8") == content:
        return SEARCH_INDEX_JSON
    SEARCH_INDEX_JSON.write_text(content, encoding="utf-8")
    return SEARCH_INDEX_JSON
