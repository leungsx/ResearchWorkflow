#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

from rendering.action_queue import write_action_queue
from rendering.archive_policy import write_archive_policy
from rendering.collaboration import write_collaboration_state
from rendering.paths import ARCHIVE_POLICY_HTML, ARCHIVE_POLICY_JSON, COLLABORATION_HTML, COLLABORATION_JSON, WORKFLOW_AUDIT_JSON
from rendering.schemas import validate_workflow_schemas
from rendering.ui import render_shell
from rendering.workflow_state import write_workflow_state


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
PROJECTS = ROOT / "projects"
PAPER_READING = ROOT / "paper_reading"
KNOWLEDGE_CARDS = ROOT / "knowledge_cards"
KNOWLEDGE_GRAPH = ROOT / "knowledge_graph"
SEARCH = ROOT / "search"
HTML_LOGS = ROOT / "logs"
GRAPH_DIR = VAULT / "13_Knowledge_Graph"
ARTIFACT_MANIFEST = GRAPH_DIR / "artifact_manifest.csv"
SEARCH_INDEX = GRAPH_DIR / "search_index.json"
ACTION_QUEUE = GRAPH_DIR / "action_queue.json"
COLLABORATION_STATE = COLLABORATION_JSON
ARCHIVE_POLICY = ARCHIVE_POLICY_JSON
AUDIT_REPORT_JSON = WORKFLOW_AUDIT_JSON
REVIEW_QUEUE = VAULT / "14_Review_Queue" / "review_queue.csv"
REVIEW_STATE = VAULT / "14_Review_Queue" / "review_state.json"
REVIEW_TODAY = KNOWLEDGE_CARDS / "review_today.html"
AUDIT_DIR = VAULT / "07_Codex_Logs" / "workflow_audits"
COMPACT_DIR = VAULT / "07_Codex_Logs" / "compact_daily"
DAILY_DIR = VAULT / "07_Codex_Logs" / "daily"
SWEEP_DIR = VAULT / "07_Codex_Logs" / "file_sweeps"
PACK_DIR = VAULT / "09_Context_Packs"
BACKUP_DIR = ROOT / "backups"
HEALTH_HTML = ROOT / "workflow_health.html"
WORKFLOW_STATE_HTML = ROOT / "workflow_state.html"
ACTION_QUEUE_HTML = ROOT / "action_queue.html"
COLLABORATION_PAGE = COLLABORATION_HTML
ARCHIVE_POLICY_PAGE = ARCHIVE_POLICY_HTML
STATE_HASH_TARGETS = [GRAPH_DIR / "workflow_state.json", ACTION_QUEUE, COLLABORATION_STATE, ARCHIVE_POLICY]


@dataclass
class Check:
    area: str
    status: str
    title: str
    detail: str


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def parse_date(value: str | None) -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.date.today()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except FileNotFoundError:
        return ""


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def html_links(path: Path) -> list[str]:
    parser = LinkParser()
    parser.feed(read_text(path))
    return parser.links


def is_external(href: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href))


def local_target(page: Path, href: str) -> Path | None:
    if not href or href.startswith("#") or is_external(href):
        return None
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return None
    return (page.parent / unquote(clean)).resolve()


def user_facing_html_pages() -> list[Path]:
    pages = [
        ROOT / "study_dashboard.html",
        ROOT / "workflow_health.html",
        PAPER_READING / "today.html",
        PAPER_READING / "index.html",
        KNOWLEDGE_CARDS / "index.html",
        REVIEW_TODAY,
        KNOWLEDGE_GRAPH / "index.html",
        SEARCH / "index.html",
        WORKFLOW_STATE_HTML,
        ACTION_QUEUE_HTML,
        COLLABORATION_PAGE,
        ARCHIVE_POLICY_PAGE,
        HTML_LOGS / "index.html",
    ]
    pages.extend(sorted(PAPER_READING.glob("20*.html")))
    pages.extend(sorted(HTML_LOGS.glob("20*.html")))
    return [path for path in pages if path.exists()]


def all_generated_html_pages() -> list[Path]:
    pages = user_facing_html_pages()
    for directory in [
        PAPER_READING / "views",
        PAPER_READING / "views" / "directories",
        KNOWLEDGE_CARDS / "views",
        HTML_LOGS / "views",
        SEARCH,
    ]:
        pages.extend(sorted(directory.glob("*.html")))
    return sorted(set(pages))


def add(checks: list[Check], area: str, status: str, title: str, detail: str) -> None:
    checks.append(Check(area, status, title, detail))


def check_required_files(checks: list[Check], day: dt.date) -> None:
    required = [
        ROOT / "study_dashboard.html",
        PAPER_READING / "today.html",
        PAPER_READING / "index.html",
        KNOWLEDGE_CARDS / "index.html",
        REVIEW_TODAY,
        KNOWLEDGE_GRAPH / "index.html",
        SEARCH / "index.html",
        COLLABORATION_PAGE,
        ARCHIVE_POLICY_PAGE,
        HTML_LOGS / "index.html",
        DAILY_DIR / f"{day.isoformat()}.md",
        COMPACT_DIR / f"{day.isoformat()}-summary.md",
        PACK_DIR / f"{day.isoformat()}-context-pack.md",
        SWEEP_DIR / f"{day.isoformat()}-file-sweep.md",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        add(checks, "入口/归档", "FAIL", "必需入口或归档文件缺失", "；".join(missing))
    else:
        add(checks, "入口/归档", "PASS", "必需入口和今日归档齐全", f"{len(required)} 个关键文件存在。")


def check_user_facing_markdown_links(checks: list[Check]) -> None:
    offenders: list[str] = []
    for page in user_facing_html_pages():
        for href in html_links(page):
            if href.endswith(".md") or ".md#" in href:
                offenders.append(f"{rel(page)} -> {href}")
    if offenders:
        add(checks, "易用性", "FAIL", "用户入口仍有裸 Markdown 链接", "\n".join(offenders[:20]))
    else:
        add(checks, "易用性", "PASS", "用户入口没有裸 Markdown 直链", "主入口、今日页、知识卡、复习、图谱、搜索和日志入口都指向可浏览页面。")


def check_local_link_targets(checks: list[Check]) -> None:
    missing: list[str] = []
    for page in all_generated_html_pages():
        for href in html_links(page):
            target = local_target(page, href)
            if target == HEALTH_HTML.resolve():
                continue
            if target and target.is_relative_to(ROOT) and not target.exists():
                missing.append(f"{rel(page)} -> {href}")
    if missing:
        add(checks, "链接健康", "FAIL", "HTML 页面存在失效本地链接", "\n".join(missing[:30]))
    else:
        add(checks, "链接健康", "PASS", "HTML 本地链接均可解析", f"检查 {len(all_generated_html_pages())} 个 HTML 页面。")


def source_from_view(view: Path) -> Path | None:
    match = re.search(r'<div class="source-path">源文件：([^<]+)</div>', read_text(view, limit=200_000))
    if not match:
        return None
    return (ROOT / html.unescape(match.group(1))).resolve()


def check_mirror_freshness(checks: list[Check]) -> None:
    stale: list[str] = []
    missing: list[str] = []
    total = 0
    for directory in [PAPER_READING / "views", KNOWLEDGE_CARDS / "views", HTML_LOGS / "views"]:
        for view in sorted(directory.glob("*.html")):
            source = source_from_view(view)
            if not source:
                continue
            total += 1
            if not source.exists():
                missing.append(f"{rel(view)} -> {rel(source)}")
            elif source.stat().st_mtime > view.stat().st_mtime + 2:
                stale.append(f"{rel(view)} older than {rel(source)}")
    if missing:
        add(checks, "镜像页", "FAIL", "HTML 镜像源文件缺失", "\n".join(missing[:20]))
    elif stale:
        add(checks, "镜像页", "WARN", "HTML 镜像可能过期", "\n".join(stale[:20]))
    else:
        add(checks, "镜像页", "PASS", "HTML 镜像与源文件同步", f"检查 {total} 个镜像页。")


def check_graph(checks: list[Check]) -> None:
    graph_html = KNOWLEDGE_GRAPH / "index.html"
    graph_text = read_text(graph_html)
    markers = ['id="graphSvg"', "const graphData", 'data-kind="concept"', "关系图谱"]
    missing_markers = [marker for marker in markers if marker not in graph_text]
    nodes = csv_rows(GRAPH_DIR / "obsidian_nodes.csv")
    edges = csv_rows(GRAPH_DIR / "obsidian_edges.csv")
    edge_keys = [(row.get("Source", ""), row.get("Target", ""), row.get("Label", "")) for row in edges]
    duplicate_count = len(edge_keys) - len(set(edge_keys))
    if missing_markers:
        add(checks, "知识图谱", "FAIL", "图谱入口缺少交互式可视化标记", "；".join(missing_markers))
    elif duplicate_count:
        add(checks, "知识图谱", "WARN", "图谱 CSV 存在重复边", f"{duplicate_count} duplicate edge rows; run make obsidian-graph after exporter fix.")
    elif not nodes or not edges:
        add(checks, "知识图谱", "FAIL", "图谱节点或关系为空", f"nodes={len(nodes)}, edges={len(edges)}")
    else:
        add(checks, "知识图谱", "PASS", "图谱入口是可视化关系图", f"nodes={len(nodes)}, unique_edges={len(edges)}")


def check_artifact_manifest(checks: list[Check]) -> None:
    rows = csv_rows(ARTIFACT_MANIFEST)
    if not rows:
        add(checks, "资产清单", "FAIL", "artifact manifest 缺失或为空", f"期望文件：{rel(ARTIFACT_MANIFEST)}")
        return

    required_fields = {"source_path", "source_type", "display_path", "display_type", "title", "layer", "generated_by"}
    missing_fields = required_fields - set(rows[0].keys())
    display_missing: list[str] = []
    source_missing: list[str] = []
    markdown_displays: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    duplicates: list[str] = []
    display_types = {row.get("display_type", "") for row in rows}

    for row in rows:
        source_path = row.get("source_path", "")
        display_path = row.get("display_path", "")
        display_type = row.get("display_type", "")
        key = (source_path, display_path, display_type)
        if key in seen:
            duplicates.append(" | ".join(key))
        seen.add(key)

        if display_path.endswith(".md"):
            markdown_displays.append(f"{source_path} -> {display_path}")
        if display_path and not (ROOT / display_path).exists():
            display_missing.append(f"{source_path} -> {display_path}")
        if source_path and not (ROOT / source_path).exists():
            source_missing.append(source_path)

    required_types = {
        "dashboard",
        "paper_today_entry",
        "knowledge_cards_index",
        "review_today",
        "knowledge_graph",
        "search",
        "logs_index",
        "review_state",
        "search_index",
        "workflow_state",
        "workflow_state_data",
        "action_queue",
        "action_queue_data",
        "project_collaboration",
        "project_collaboration_data",
        "archive_policy",
        "archive_policy_data",
        "page_verification_queue",
        "workflow_audit_data",
    }
    missing_types = sorted(required_types - display_types)
    failures = []
    if missing_fields:
        failures.append("缺少字段：" + "、".join(sorted(missing_fields)))
    if display_missing:
        failures.append("缺失展示页：" + "；".join(display_missing[:8]))
    if markdown_displays:
        failures.append("展示路径指向 Markdown：" + "；".join(markdown_displays[:8]))
    if missing_types:
        failures.append("缺少展示类型：" + "、".join(missing_types))
    if duplicates:
        failures.append("重复条目：" + "；".join(duplicates[:5]))

    if failures:
        add(checks, "资产清单", "FAIL", "artifact manifest 不满足展示契约", "；".join(failures))
    elif source_missing:
        add(checks, "资产清单", "WARN", "manifest 中存在源文件缺失", "；".join(source_missing[:8]))
    else:
        add(checks, "资产清单", "PASS", "artifact manifest 覆盖核心展示资产", f"{len(rows)} 条；display_types={len(display_types)}")


def check_search_index(checks: list[Check]) -> None:
    payload = read_json(SEARCH_INDEX)
    search_html = SEARCH / "index.html"
    search_text = read_text(search_html)
    if not isinstance(payload, dict):
        add(checks, "搜索索引", "FAIL", "search_index.json 缺失或不是合法 JSON", rel(SEARCH_INDEX))
        return
    entries = payload.get("entries", [])
    if not isinstance(entries, list) or not entries:
        add(checks, "搜索索引", "FAIL", "搜索索引为空", rel(SEARCH_INDEX))
        return
    if not search_html.exists() or "searchInput" not in search_text or "searchState" not in search_text:
        add(checks, "搜索索引", "FAIL", "搜索 HTML 入口缺少交互标记", rel(search_html))
        return

    bad_targets: list[str] = []
    markdown_targets: list[str] = []
    missing_text: list[str] = []
    for entry in entries:
        display_path = str(entry.get("display_path", ""))
        title = str(entry.get("title", ""))
        if not display_path.endswith(".html"):
            markdown_targets.append(f"{title} -> {display_path}")
        if display_path and not (ROOT / display_path).exists():
            bad_targets.append(f"{title} -> {display_path}")
        if not entry.get("search_text"):
            missing_text.append(title or display_path)

    declared_count = payload.get("entry_count")
    if declared_count != len(entries):
        add(checks, "搜索索引", "FAIL", "搜索索引计数不一致", f"entry_count={declared_count}, actual={len(entries)}")
    elif bad_targets or markdown_targets:
        detail = []
        if bad_targets:
            detail.append("失效展示目标：" + "；".join(bad_targets[:8]))
        if markdown_targets:
            detail.append("非 HTML 展示目标：" + "；".join(markdown_targets[:8]))
        add(checks, "搜索索引", "FAIL", "搜索结果目标不满足 HTML 契约", "；".join(detail))
    elif missing_text:
        add(checks, "搜索索引", "WARN", "部分搜索条目缺少 search_text", "；".join(missing_text[:8]))
    else:
        layers = sorted({str(entry.get("layer", "")) for entry in entries if entry.get("layer")})
        add(checks, "搜索索引", "PASS", "搜索索引和搜索页可用", f"{len(entries)} 条；layers={len(layers)}")


def check_review_state(checks: list[Check], day: dt.date) -> None:
    queue_rows = csv_rows(REVIEW_QUEUE)
    payload = read_json(REVIEW_STATE)
    if not isinstance(payload, dict):
        add(checks, "复习状态", "FAIL", "review_state.json 缺失或不是合法 JSON", rel(REVIEW_STATE))
        return
    if not REVIEW_TODAY.exists() or "今日复习入口" not in read_text(REVIEW_TODAY):
        add(checks, "复习状态", "FAIL", "今日复习 HTML 入口缺失或内容异常", rel(REVIEW_TODAY))
        return

    summary = payload.get("summary", {})
    today = day.isoformat()
    expected_due = sum(1 for row in queue_rows if row.get("next_review", "") <= today and row.get("last_reviewed", "") != today)
    total = summary.get("total_items")
    due_count = summary.get("due_count")
    focus_items = payload.get("focus_items", [])
    bad_focus: list[str] = []
    if isinstance(focus_items, list):
        for item in focus_items:
            display_path = str(item.get("display_path", ""))
            if not display_path.endswith(".html") or not (ROOT / display_path).exists():
                bad_focus.append(f"{item.get('title', '')} -> {display_path}")

    if total != len(queue_rows) or due_count != expected_due:
        add(checks, "复习状态", "FAIL", "review_state 与 review_queue 不一致", f"total={total}/{len(queue_rows)}；due={due_count}/{expected_due}")
    elif bad_focus:
        add(checks, "复习状态", "FAIL", "复习重点项展示目标失效", "；".join(bad_focus[:8]))
    else:
        add(checks, "复习状态", "PASS", "复习状态快照与队列一致", f"total={total}, due={due_count}, focus={len(focus_items) if isinstance(focus_items, list) else 0}")


def check_project_states(checks: list[Check]) -> None:
    projects = sorted([path for path in PROJECTS.iterdir() if path.is_dir() and (path / "project.yaml").exists()])
    if not projects:
        add(checks, "项目状态", "WARN", "未发现 project.yaml 项目", "projects/ 下没有可审计项目。")
        return

    problems: list[str] = []
    for project in projects:
        state_path = project / "project_state.json"
        payload = read_json(state_path)
        if not isinstance(payload, dict):
            problems.append(f"{project.name}: project_state.json 缺失或 JSON 无效")
            continue
        entrypoints = payload.get("entrypoints", {})
        artifacts = payload.get("artifacts", {})
        for key in ["today", "project_dashboard", "review_today", "search"]:
            value = str(entrypoints.get(key, ""))
            if not value or not value.endswith(".html") or not (ROOT / value).exists():
                problems.append(f"{project.name}: entrypoints.{key} -> {value}")
        for key in ["artifact_manifest", "search_index"]:
            value = str(artifacts.get(key, entrypoints.get(key, "")))
            if not value or not (ROOT / value).exists():
                problems.append(f"{project.name}: {key} -> {value}")
        review = payload.get("review", {})
        if not isinstance(review, dict) or "focus_items" not in review:
            problems.append(f"{project.name}: review.focus_items 缺失")

    if problems:
        add(checks, "项目状态", "FAIL", "项目状态文件缺少关键入口", "；".join(problems[:10]))
    else:
        add(checks, "项目状态", "PASS", "项目状态文件可供自动化读取", f"{len(projects)} 个项目。")


def check_action_queue(checks: list[Check]) -> None:
    payload = read_json(ACTION_QUEUE)
    if not isinstance(payload, dict):
        add(checks, "行动队列", "FAIL", "action_queue.json 缺失或不是合法 JSON", rel(ACTION_QUEUE))
        return
    if not ACTION_QUEUE_HTML.exists() or "行动队列" not in read_text(ACTION_QUEUE_HTML):
        add(checks, "行动队列", "FAIL", "行动队列 HTML 入口缺失或内容异常", rel(ACTION_QUEUE_HTML))
        return
    actions = payload.get("actions", [])
    if not isinstance(actions, list) or not actions:
        add(checks, "行动队列", "WARN", "行动队列为空", "如果审计和复习都无积压，可以接受；否则需检查生成器。")
        return
    bad_targets: list[str] = []
    for action in actions:
        entrypoint = str(action.get("entrypoint", ""))
        if not entrypoint.endswith(".html") or not (ROOT / entrypoint).exists():
            bad_targets.append(f"{action.get('title', '')} -> {entrypoint}")
    summary = payload.get("summary", {})
    if summary.get("total_open") != len(actions):
        add(checks, "行动队列", "FAIL", "行动队列计数不一致", f"total_open={summary.get('total_open')}, actual={len(actions)}")
    elif bad_targets:
        add(checks, "行动队列", "FAIL", "行动队列存在非 HTML 或失效入口", "；".join(bad_targets[:8]))
    else:
        add(checks, "行动队列", "PASS", "行动队列可用且入口有效", f"{len(actions)} 个开放行动。")


def check_collaboration_state(checks: list[Check]) -> None:
    payload = read_json(COLLABORATION_STATE)
    if not isinstance(payload, dict):
        add(checks, "项目协作层", "FAIL", "collaboration_state.json 缺失或不是合法 JSON", rel(COLLABORATION_STATE))
        return
    if not COLLABORATION_PAGE.exists() or "项目协作层" not in read_text(COLLABORATION_PAGE):
        add(checks, "项目协作层", "FAIL", "项目协作 HTML 入口缺失或内容异常", rel(COLLABORATION_PAGE))
        return
    projects = payload.get("projects", [])
    if not isinstance(projects, list):
        add(checks, "项目协作层", "FAIL", "collaboration_state.projects 不是数组", rel(COLLABORATION_STATE))
        return
    bad_targets: list[str] = []
    for project in projects:
        entrypoints = project.get("entrypoints", {}) if isinstance(project, dict) else {}
        for key, value in entrypoints.items():
            path = str(value or "")
            if path and (not path.endswith(".html") or not (ROOT / path).exists()):
                bad_targets.append(f"{project.get('slug', '')}.{key} -> {path}")
    summary = payload.get("summary", {})
    if summary.get("project_count") != len(projects):
        add(checks, "项目协作层", "FAIL", "协作层项目计数不一致", f"project_count={summary.get('project_count')}, actual={len(projects)}")
    elif bad_targets:
        add(checks, "项目协作层", "FAIL", "协作层存在失效或非 HTML 入口", "；".join(bad_targets[:8]))
    else:
        add(checks, "项目协作层", "PASS", "项目协作层可用", f"{len(projects)} 个项目；user_waiting={summary.get('user_waiting', 0)}。")


def check_archive_policy(checks: list[Check]) -> None:
    payload = read_json(ARCHIVE_POLICY)
    if not isinstance(payload, dict):
        add(checks, "自动归档策略", "FAIL", "archive_policy.json 缺失或不是合法 JSON", rel(ARCHIVE_POLICY))
        return
    if not ARCHIVE_POLICY_PAGE.exists() or "自动归档策略" not in read_text(ARCHIVE_POLICY_PAGE):
        add(checks, "自动归档策略", "FAIL", "自动归档策略 HTML 入口缺失或内容异常", rel(ARCHIVE_POLICY_PAGE))
        return
    summary = payload.get("summary", {})
    actions = payload.get("actions", [])
    if not isinstance(actions, list) or not actions:
        add(checks, "自动归档策略", "FAIL", "归档策略缺少建议动作", rel(ARCHIVE_POLICY))
    elif "backup_count" not in summary or "cache_candidates" not in summary:
        add(checks, "自动归档策略", "FAIL", "归档策略 summary 缺少关键计数", rel(ARCHIVE_POLICY))
    else:
        detail = f"backup={summary.get('backup_count', 0)}, prune={summary.get('backup_prune_candidates', 0)}, cache={summary.get('cache_candidates', 0)}"
        add(checks, "自动归档策略", "PASS", "自动归档策略可用", detail)


def check_review_queue(checks: list[Check], day: dt.date) -> None:
    rows = csv_rows(REVIEW_QUEUE)
    today = day.isoformat()
    due = [row for row in rows if row.get("next_review", "") <= today and row.get("last_reviewed", "") != today]
    if not rows:
        add(checks, "复习队列", "WARN", "复习队列为空", "新增知识卡后应写入 review_queue.csv。")
    elif due:
        names = "；".join(row.get("title", row.get("id", "")) for row in due[:8])
        add(checks, "复习队列", "WARN", "存在到期复习项", f"{len(due)} 项到期：{names}")
    else:
        add(checks, "复习队列", "PASS", "今日无积压复习项", f"队列共 {len(rows)} 项。")


def check_backup(checks: list[Check], day: dt.date) -> None:
    backups = sorted(BACKUP_DIR.glob("**/*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not backups:
        add(checks, "备份", "WARN", "尚未发现工作流备份包", "建议运行 make workflow-backup。")
        return
    latest = backups[0]
    age_hours = (dt.datetime.now().timestamp() - latest.stat().st_mtime) / 3600
    if age_hours > 36:
        add(checks, "备份", "WARN", "最近备份超过 36 小时", f"{rel(latest)}，约 {age_hours:.1f} 小时前。")
    else:
        add(checks, "备份", "PASS", "最近备份可用", f"{rel(latest)}，约 {age_hours:.1f} 小时前。")


def check_context_budget(checks: list[Check], day: dt.date) -> None:
    context_index = ROOT / "codex" / "state" / "context_index.md"
    compact = COMPACT_DIR / f"{day.isoformat()}-summary.md"
    if not context_index.exists() or not compact.exists():
        add(checks, "Token/记忆", "WARN", "上下文压缩索引不完整", "运行 make codex-compact DATE=<date> && make codex-context-index。")
    else:
        words = len(read_text(compact).split())
        status = "PASS" if words <= 900 else "WARN"
        add(checks, "Token/记忆", status, "今日 compact summary 可作为默认启动上下文", f"{rel(compact)}，约 {words} words。")


def git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def check_git_backup(checks: list[Check]) -> None:
    inside = git_command(["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        add(checks, "Git/异地备份", "WARN", "当前目录尚未启用 Git", "运行 git init 并连接私有远程仓库后，可获得提交级回溯。")
        return

    status = git_command(["status", "--porcelain"])
    dirty = [line for line in status.stdout.splitlines() if line.strip()]
    remote = git_command(["remote", "get-url", "origin"])
    remote_url = remote.stdout.strip()
    branch_status = git_command(["status", "--porcelain=v2", "--branch"]).stdout.splitlines()
    upstream = ""
    ahead = 0
    behind = 0
    for line in branch_status:
        if line.startswith("# branch.upstream "):
            upstream = line.removeprefix("# branch.upstream ").strip()
        elif line.startswith("# branch.ab "):
            parts = line.split()
            for part in parts:
                if part.startswith("+"):
                    ahead = int(part[1:])
                elif part.startswith("-"):
                    behind = int(part[1:])
    latest = git_command(["log", "-1", "--format=%h %ci %s"])
    latest_line = latest.stdout.strip() if latest.returncode == 0 else "no commits yet"

    if dirty:
        sample = "；".join(dirty[:8])
        add(checks, "Git/异地备份", "WARN", "存在尚未提交的 Git 改动", f"{len(dirty)} 个路径待快照：{sample}")
    elif not remote_url:
        add(checks, "Git/异地备份", "WARN", "Git 已启用但未连接 origin 远程", f"last commit: {latest_line}")
    elif not upstream:
        add(checks, "Git/异地备份", "WARN", "origin 已配置但当前分支未设置 upstream", f"{remote_url}；last commit: {latest_line}")
    elif ahead:
        add(checks, "Git/异地备份", "WARN", "本地提交尚未推送到远程", f"ahead={ahead}, behind={behind}；remote={remote_url}")
    elif behind:
        add(checks, "Git/异地备份", "WARN", "远程可能有本地未同步提交", f"ahead={ahead}, behind={behind}；remote={remote_url}")
    else:
        add(checks, "Git/异地备份", "PASS", "Git 本地和远程快照状态正常", f"upstream={upstream}；last commit: {latest_line}")


def check_hygiene(checks: list[Check]) -> None:
    ds_store = list(ROOT.rglob(".DS_Store"))
    pycache = [path for path in ROOT.rglob("__pycache__") if path.is_dir()]
    detail = []
    if ds_store:
        detail.append(f".DS_Store={len(ds_store)}")
    if pycache:
        detail.append(f"__pycache__={len(pycache)}")
    if detail:
        add(checks, "文件卫生", "WARN", "工作区存在系统/缓存文件", "；".join(detail) + "；这些不会进入 file sweep，但可择机清理。")
    else:
        add(checks, "文件卫生", "PASS", "未发现常见系统/缓存文件", "工作区较干净。")


def run_checks(day: dt.date) -> list[Check]:
    checks: list[Check] = []
    check_required_files(checks, day)
    check_user_facing_markdown_links(checks)
    check_local_link_targets(checks)
    check_mirror_freshness(checks)
    check_graph(checks)
    check_artifact_manifest(checks)
    check_search_index(checks)
    check_review_state(checks, day)
    check_project_states(checks)
    check_review_queue(checks, day)
    check_backup(checks, day)
    check_git_backup(checks)
    check_context_budget(checks, day)
    check_hygiene(checks)
    return checks


def status_counts(checks: list[Check]) -> dict[str, int]:
    return {status: sum(1 for check in checks if check.status == status) for status in ["PASS", "WARN", "FAIL"]}


def state_bundle_hash() -> str:
    digest = hashlib.sha256()
    for path in STATE_HASH_TARGETS:
        digest.update(rel(path).encode("utf-8"))
        if path.exists():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing>")
    return digest.hexdigest()


def check_schema_validation(checks: list[Check]) -> None:
    report = validate_workflow_schemas()
    failures = [issue for issue in report.issues if issue.status == "FAIL"]
    warnings = [issue for issue in report.issues if issue.status == "WARN"]
    if failures:
        detail = "；".join(f"{issue.path}: {issue.message}" for issue in failures[:10])
        add(checks, "Schema", "FAIL", "核心机器状态 schema 校验失败", detail)
    elif warnings:
        detail = "；".join(f"{issue.path}: {issue.message}" for issue in warnings[:10])
        add(checks, "Schema", "WARN", "核心机器状态 schema 存在提醒", detail)
    else:
        add(checks, "Schema", "PASS", "核心机器状态 schema 校验通过", f"{len(report.checked_files)} 个文件通过校验。")


def audit_report_payload(day: dt.date, checks: list[Check], md_path: Path, html_path: Path, audit_mode: str, pre_state_hash: str, post_state_hash: str) -> dict[str, object]:
    counts = status_counts(checks)
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "date": day.isoformat(),
        "audit_mode": audit_mode,
        "pre_refresh_state_hash": pre_state_hash,
        "post_refresh_state_hash": post_state_hash,
        "summary": {
            "counts": counts,
            "check_count": len(checks),
        },
        "reports": {
            "markdown": rel(md_path),
            "html": rel(html_path),
        },
        "checks": [
            {
                "area": check.area,
                "status": check.status,
                "title": check.title,
                "detail": check.detail,
            }
            for check in checks
        ],
    }


def write_audit_json(day: dt.date, checks: list[Check], md_path: Path, html_path: Path, audit_mode: str, pre_state_hash: str, post_state_hash: str) -> Path:
    AUDIT_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = audit_report_payload(day, checks, md_path, html_path, audit_mode, pre_state_hash, post_state_hash)
    AUDIT_REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return AUDIT_REPORT_JSON


def markdown_report(day: dt.date, checks: list[Check], audit_mode: str, pre_state_hash: str, post_state_hash: str) -> str:
    counts = status_counts(checks)
    lines = [
        f"# Workflow Audit - {day.isoformat()}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Audit mode: `{audit_mode}`",
        f"Pre-refresh state hash: `{pre_state_hash}`",
        f"Post-refresh state hash: `{post_state_hash}`",
        f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}",
        "",
        "## Checks",
        "",
        "| Area | Status | Check | Detail |",
        "|---|---:|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("\n", "<br>")
        lines.append(f"| {check.area} | {check.status} | {check.title} | {detail} |")
    lines.extend(
        [
            "",
            "## Recommended Daily Order",
            "",
            "1. Use `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE=\"daily closeout\"` when remote Git backup is desired.",
            "2. Use `make workflow-refresh DATE=<YYYY-MM-DD> NOTE=\"daily closeout\"` for local-only refresh.",
            "3. Use `make workflow-backup-prune KEEP=30` only when you intentionally want to reduce local backup zips.",
            "",
            "Both refresh commands are sequential no-race closeout commands; do not parallelize dashboard generation and audit.",
            "",
        ]
    )
    return "\n".join(lines)


def html_report(day: dt.date, checks: list[Check], audit_mode: str) -> str:
    counts = status_counts(checks)
    cards = "\n".join(
        f"""        <article class="check {check.status.lower()}">
          <div class="status">{check.status}</div>
          <h2>{html.escape(check.title)}</h2>
          <p class="area">{html.escape(check.area)}</p>
          <p>{html.escape(check.detail)}</p>
        </article>"""
        for check in checks
    )
    body = f"""
    <section class="metrics">
      <div class="metric"><b>{counts['PASS']}</b><span>通过</span></div>
      <div class="metric"><b>{counts['WARN']}</b><span>提醒</span></div>
      <div class="metric"><b>{counts['FAIL']}</b><span>失败</span></div>
    </section>
    <section class="checks">{cards}</section>
"""
    return render_shell(
        title="ResearchWorkflow 体检",
        subtitle="检查入口、链接、镜像页、搜索、复习队列和系统状态是否可用。",
        current="工作流体检",
        body=body,
        output=HEALTH_HTML,
        module="系统",
        meta=f"Generated {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · mode={html.escape(audit_mode)} · PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}",
        footer="Run make workflow-audit to refresh this page.",
    )


def render_state_outputs(checks: list[Check], baseline_dirty_paths: int) -> None:
    write_workflow_state(checks, git_dirty_paths=baseline_dirty_paths)
    write_action_queue()
    write_collaboration_state()
    write_archive_policy()


def write_reports(day: dt.date, checks: list[Check], refresh_state: bool) -> tuple[Path, Path, Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = AUDIT_DIR / f"{day.isoformat()}-workflow-audit.md"
    baseline_dirty_paths = len([line for line in git_command(["status", "--porcelain"]).stdout.splitlines() if line.strip()])
    audit_mode = "refresh_then_audit" if refresh_state else "readonly"
    pre_state_hash = state_bundle_hash()
    post_state_hash = pre_state_hash

    if refresh_state:
        render_state_outputs(checks, baseline_dirty_paths)
        post_state_hash = state_bundle_hash()
    md_path.write_text(markdown_report(day, checks, audit_mode, pre_state_hash, post_state_hash) + "\n", encoding="utf-8")
    HEALTH_HTML.write_text(html_report(day, checks, audit_mode), encoding="utf-8")
    write_audit_json(day, checks, md_path, HEALTH_HTML, audit_mode, pre_state_hash, post_state_hash)

    check_schema_validation(checks)
    if refresh_state:
        render_state_outputs(checks, baseline_dirty_paths)
        post_state_hash = state_bundle_hash()

    check_action_queue(checks)
    check_collaboration_state(checks)
    check_archive_policy(checks)
    if refresh_state:
        render_state_outputs(checks, baseline_dirty_paths)
        post_state_hash = state_bundle_hash()

    md_path.write_text(markdown_report(day, checks, audit_mode, pre_state_hash, post_state_hash) + "\n", encoding="utf-8")
    HEALTH_HTML.write_text(html_report(day, checks, audit_mode), encoding="utf-8")
    json_path = write_audit_json(day, checks, md_path, HEALTH_HTML, audit_mode, pre_state_hash, post_state_hash)
    return md_path, HEALTH_HTML, json_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit ResearchWorkflow usability, links, graph, archive, and backup health.")
    parser.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on WARN as well as FAIL.")
    parser.add_argument("--readonly", action="store_true", help="Do not refresh workflow/action/collaboration/archive state before auditing.")
    parser.add_argument("--refresh-state", action="store_true", help="Refresh workflow/action/collaboration/archive state during audit.")
    args = parser.parse_args()

    day = parse_date(args.date)
    checks = run_checks(day)
    refresh_state = args.refresh_state or not args.readonly
    md_path, html_path, json_path = write_reports(day, checks, refresh_state=refresh_state)
    counts = status_counts(checks)
    print(f"Wrote workflow audit: {md_path}")
    print(f"Wrote workflow health page: {html_path}")
    print(f"Wrote workflow audit data: {json_path}")
    print(f"PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    if counts["FAIL"] or (args.strict and counts["WARN"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
