#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from rendering.routes import paper_markdown_view_path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"
GRAPH_DIR = ROOT / "vault" / "13_Knowledge_Graph"
ARTIFACT_MANIFEST = GRAPH_DIR / "artifact_manifest.csv"
REVIEW_QUEUE = ROOT / "vault" / "14_Review_Queue" / "review_queue.csv"
REVIEW_STATE = ROOT / "vault" / "14_Review_Queue" / "review_state.json"
REVIEW_TODAY = ROOT / "knowledge_cards" / "review_today.html"
SEARCH_INDEX_HTML = ROOT / "search" / "index.html"
SEARCH_INDEX_JSON = GRAPH_DIR / "search_index.json"
COLLABORATION_HTML = ROOT / "project_collaboration.html"
ARCHIVE_POLICY_HTML = ROOT / "archive_policy.html"
PAPER_READING = ROOT / "paper_reading"

from rendering.review import build_review_state


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    item = Path(path)
    try:
        return str(item.relative_to(ROOT))
    except ValueError:
        return str(item)


def html_view(path: Path) -> str:
    return rel(paper_markdown_view_path(path))


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def title_from_html(path: Path) -> str:
    if not path.exists():
        return path.stem
    text = path.read_text(encoding="utf-8", errors="ignore")[:4000]
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
    if match:
        return clean(re.sub(r"<[^>]+>", "", match.group(1)))
    match = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", text)
    if match:
        return clean(re.sub(r"<[^>]+>", "", match.group(1)))
    return path.stem


def project_matrix_rows(project: str) -> list[dict[str, str]]:
    rows = read_csv(MATRIX)
    return [row for row in rows if project in row.get("project_tags", "")]


def count_existing(paths: list[str]) -> int:
    total = 0
    for value in paths:
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            total += 1
    return total


def deep_read_from_latest_state(latest: dict[str, Any]) -> dict[str, str]:
    output = clean(latest.get("output", ""))
    if not output:
        return {}
    page = Path(output)
    if not page.is_absolute():
        page = ROOT / page
    if not page.exists() or page.suffix != ".html":
        return {"path": rel(page), "title": "", "updated_at": ""}
    return {
        "title": title_from_html(page),
        "path": rel(page),
        "updated_at": dt.datetime.fromtimestamp(page.stat().st_mtime).isoformat(timespec="seconds"),
    }


def latest_learning_state(project: Path) -> dict[str, Any]:
    state = read_json(project / "literature" / "daily_learning_state.json", {"history": []})
    history = sorted(state.get("history", []), key=lambda item: item.get("date", ""))
    return {
        "path": rel(project / "literature" / "daily_learning_state.json"),
        "last_updated": state.get("last_updated", ""),
        "latest": history[-1] if history else {},
        "history_count": len(history),
    }


def evidence_summary(project: Path) -> dict[str, str]:
    path = project / "manuscript" / "evidence_gate_report.md"
    if not path.exists():
        return {"path": rel(path), "status": "missing", "error": "", "warn": ""}
    text = path.read_text(encoding="utf-8", errors="ignore")

    def metric(name: str) -> str:
        match = re.search(rf"\|\s*{re.escape(name)}\s*\|\s*([^|]+?)\s*\|", text)
        return clean(match.group(1)) if match else ""

    return {
        "path": rel(path),
        "status": metric("Status") or "unknown",
        "error": metric("ERROR issues"),
        "warn": metric("WARN issues"),
    }


def artifact_entries_for_project(project: str) -> list[dict[str, str]]:
    rows = read_csv(ARTIFACT_MANIFEST)
    keep: list[dict[str, str]] = []
    for row in rows:
        source = row.get("source_path", "")
        display = row.get("display_path", "")
        if project in source or project in display or source in {"study_dashboard.html", "paper_reading/today.html", "paper_reading/index.html"}:
            keep.append(row)
    return keep


def due_review_count() -> int:
    today = dt.date.today().isoformat()
    count = 0
    for row in read_csv(REVIEW_QUEUE):
        next_review = row.get("next_review", "")
        if next_review and next_review <= today:
            count += 1
    return count


def review_snapshot() -> dict[str, Any]:
    state = build_review_state()
    summary = state.get("summary", {})
    return {
        "due_count": summary.get("due_count", 0),
        "overdue_count": summary.get("overdue_count", 0),
        "upcoming_7_count": summary.get("upcoming_7_count", 0),
        "queue_path": rel(REVIEW_QUEUE),
        "state_path": rel(REVIEW_STATE),
        "review_today": rel(REVIEW_TODAY),
        "focus_items": [
            {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "type": item.get("type", ""),
                "next_review": item.get("next_review", ""),
                "prompt": item.get("prompt", ""),
                "display_path": item.get("display_path", ""),
            }
            for item in state.get("focus_items", [])[:10]
        ],
    }


def reader_count(project: Path) -> int:
    return len([path for path in (project / "literature" / "readers").glob("*/paper.md") if path.is_file()])


def context_pack_count(project: Path) -> int:
    return len([path for path in (project / "literature" / "context_packs").glob("*.md") if path.is_file()])


def next_reading_candidates(rows: list[dict[str, str]], limit: int = 5) -> list[dict[str, str]]:
    priority = {"metadata-only": 0, "": 1, "skimmed": 2, "human-read": 3, "verified": 4}
    target_terms = ("传播力", "传播及互动", "互动效果", "服务价值", "评价", "指标", "DCI", "C指数")

    def target_score(row: dict[str, str]) -> int:
        haystack = f"{row.get('title', '')} {row.get('keywords', '')} {row.get('abstract', '')}"
        return sum(1 for term in target_terms if term in haystack)

    candidates = sorted(
        rows,
        key=lambda row: (
            0 if row.get("pdf_path") or row.get("note_path") else 1,
            -target_score(row),
            priority.get(clean(row.get("read_status")), 9),
            row.get("year", ""),
            row.get("citekey", ""),
        ),
        reverse=False,
    )
    result: list[dict[str, str]] = []
    for row in candidates:
        status = clean(row.get("read_status"))
        if status in {"verified", "human-read"}:
            continue
        result.append(
            {
                "citekey": row.get("citekey", ""),
                "title": row.get("title", ""),
                "year": row.get("year", ""),
                "source": row.get("source", ""),
                "read_status": status or "blank",
                "reader_path": rel(row.get("note_path", "")),
                "pdf_path": rel(row.get("pdf_path", "")),
            }
        )
        if len(result) >= limit:
            break
    return result


def research_questions_converged(project: Path) -> bool:
    path = project / "01_research_question.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "## Converged Main Question" in text


def latest_primary_links_done(primary: str) -> bool:
    if not primary:
        return False
    path = ROOT / "vault" / "01_Literature" / f"{primary}.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "## Knowledge Links" in text and "## 证据和边界" in text


def next_actions(project: Path, rows: list[dict[str, str]], state: dict[str, Any], evidence: dict[str, str]) -> list[str]:
    actions: list[str] = []
    if not rows:
        return [
            "先建立或导入项目文献矩阵，再生成 Reader、上下文包和阅读看板。",
            "如果这是占位项目，保持 project_state.json 作为结构模板即可。",
        ]
    statuses = Counter(clean(row.get("read_status")) or "blank" for row in rows)
    if evidence.get("status") not in {"PASS", "pass"}:
        actions.append("先处理 evidence gate 的 WARN/ERROR，避免 metadata-only 文献进入论文主张。")
    if statuses.get("skimmed", 0) >= 6 and not research_questions_converged(project):
        actions.append("把已读文献继续汇总进文献综述工作台，收敛 2-3 个研究问题。")
    latest = state.get("latest") or {}
    if latest.get("primary") and not latest_primary_links_done(str(latest["primary"])):
        actions.append(f"围绕最近主读 `{latest['primary']}`，补齐与既有概念/方法的关系和证据边界。")
    actions.append("下一篇阅读优先选择已有 PDF/Reader 且能推进传播力评价或服务价值指标的文献。")
    return actions[:4]


def build_state(project_slug: str) -> dict[str, Any]:
    project = PROJECTS / project_slug
    if not project.exists():
        raise FileNotFoundError(f"Project not found: {project}")
    meta = parse_simple_yaml(project / "project.yaml")
    rows = project_matrix_rows(project_slug)
    statuses = Counter(clean(row.get("read_status")) or "blank" for row in rows)
    state = latest_learning_state(project)
    evidence = evidence_summary(project)
    artifacts = artifact_entries_for_project(project_slug)
    deep_read = deep_read_from_latest_state(state.get("latest") or {})
    pdf_count = count_existing([row.get("pdf_path", "") for row in rows])
    dashboard = project / "00_project_dashboard.md"
    reading_board = project / "literature" / "reading_board.md"
    literature_workbench = project / "literature" / "literature_review_workbench.md"
    literature_synthesis = project / "03_literature_synthesis.md"

    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "project": {
            "slug": project_slug,
            "title": meta.get("title", project_slug),
            "status": meta.get("status", ""),
            "created_at": meta.get("created_at", ""),
            "path": rel(project),
            "dashboard": rel(dashboard),
        },
        "entrypoints": {
            "study_dashboard": "study_dashboard.html",
            "today": "paper_reading/today.html",
            "project_dashboard": html_view(dashboard),
            "reading_board": html_view(reading_board) if reading_board.exists() else "",
            "literature_workbench": html_view(literature_workbench) if literature_workbench.exists() else "",
            "literature_synthesis": html_view(literature_synthesis) if literature_synthesis.exists() else "",
            "review_today": rel(REVIEW_TODAY),
            "search": rel(SEARCH_INDEX_HTML),
            "project_collaboration": rel(COLLABORATION_HTML),
            "archive_policy": rel(ARCHIVE_POLICY_HTML),
        },
        "source_documents": {
            "project_dashboard": rel(dashboard),
            "reading_board": rel(reading_board) if reading_board.exists() else "",
            "literature_workbench": rel(literature_workbench) if literature_workbench.exists() else "",
            "literature_synthesis": rel(literature_synthesis) if literature_synthesis.exists() else "",
        },
        "literature": {
            "matrix_rows": len(rows),
            "read_status_counts": dict(sorted(statuses.items())),
            "recorded_full_texts": pdf_count,
            "reader_packages": reader_count(project),
            "context_packs": context_pack_count(project),
            "latest_recommendation": state,
            "latest_deep_read": deep_read,
            "next_reading_candidates": next_reading_candidates(rows),
        },
        "evidence_gate": evidence,
        "review": review_snapshot(),
        "artifacts": {
            "artifact_manifest": rel(ARTIFACT_MANIFEST),
            "manifest_path": rel(ARTIFACT_MANIFEST),
            "search_index": rel(SEARCH_INDEX_JSON),
            "project_related_entries": len(artifacts),
            "html_entries": [
                {
                    "source_path": row.get("source_path", ""),
                    "display_path": row.get("display_path", ""),
                    "display_type": row.get("display_type", ""),
                    "title": row.get("title", ""),
                }
                for row in artifacts[:30]
            ],
        },
        "next_actions": next_actions(project, rows, state, evidence),
    }


def write_state(project_slug: str) -> Path:
    project = PROJECTS / project_slug
    state = build_state(project_slug)
    output = project / "project_state.json"
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def project_slugs() -> list[str]:
    return sorted([path.name for path in PROJECTS.iterdir() if path.is_dir() and (path / "project.yaml").exists()])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build machine-readable project state files.")
    parser.add_argument("--project", help="Project slug")
    parser.add_argument("--all", action="store_true", help="Build states for every project with project.yaml")
    args = parser.parse_args()

    if args.all:
        slugs = project_slugs()
    elif args.project:
        slugs = [args.project]
    else:
        raise SystemExit("Use --project <slug> or --all")

    for slug in slugs:
        output = write_state(slug)
        print(f"Wrote project state: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
