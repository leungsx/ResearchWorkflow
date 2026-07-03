from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

from rendering.io import write_json_if_changed, write_text_if_changed
from rendering.paths import (
    ACTION_QUEUE_HTML,
    ACTION_QUEUE_JSON,
    REVIEW_TODAY,
    ROOT,
    SEARCH_INDEX_HTML,
    WORKFLOW_HEALTH,
    WORKFLOW_STATE_HTML,
    WORKFLOW_STATE_JSON,
)
from rendering.ui import render_shell
from rendering.workflow_state import build_workflow_state, read_json, rel


def action_id(kind: str, title: str, index: int) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in title)[:42].strip("-")
    return f"{kind}-{index + 1}-{safe or 'item'}"


def add_action(actions: list[dict[str, Any]], *, kind: str, priority: int, title: str, reason: str, entrypoint: str, source: str = "") -> None:
    actions.append(
        {
            "id": action_id(kind, title, len(actions)),
            "kind": kind,
            "priority": priority,
            "title": title,
            "reason": reason,
            "entrypoint": entrypoint,
            "source": source,
            "status": "open",
        }
    )


def build_action_queue(state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = state or read_json(WORKFLOW_STATE_JSON, {}) or build_workflow_state()
    actions: list[dict[str, Any]] = []
    audit = state.get("audit", {}) if isinstance(state, dict) else {}
    checks = audit.get("checks", []) if isinstance(audit, dict) else []
    for check in checks:
        status = check.get("status")
        if status == "FAIL":
            add_action(
                actions,
                kind="audit_fail",
                priority=100,
                title=f"修复审计失败：{check.get('title', '')}",
                reason=check.get("detail", ""),
                entrypoint=rel(WORKFLOW_HEALTH),
                source=check.get("area", ""),
            )
        elif status == "WARN" and check.get("area") in {"复习队列", "Git/异地备份", "备份"}:
            add_action(
                actions,
                kind="audit_warn",
                priority=70,
                title=f"处理提醒：{check.get('title', '')}",
                reason=check.get("detail", ""),
                entrypoint=rel(WORKFLOW_HEALTH),
                source=check.get("area", ""),
            )

    review = state.get("review", {}) if isinstance(state, dict) else {}
    review_summary = review.get("summary", {}) if isinstance(review, dict) else {}
    focus_items = review.get("focus_items", []) if isinstance(review, dict) else []
    if review_summary.get("due_count", 0):
        add_action(
            actions,
            kind="review",
            priority=90,
            title=f"完成 {review_summary.get('due_count')} 个到期知识卡复习",
            reason="先主动回忆，再打开知识卡核对概念、误区和研究用法。",
            entrypoint=rel(REVIEW_TODAY),
            source=review.get("state_path", ""),
        )
        for item in focus_items[:5]:
            add_action(
                actions,
                kind="review_item",
                priority=80,
                title=f"复习：{item.get('title', '')}",
                reason=item.get("prompt", ""),
                entrypoint=item.get("display_path", rel(REVIEW_TODAY)),
                source=item.get("source_path", ""),
            )

    for project in state.get("projects", []) if isinstance(state, dict) else []:
        slug = project.get("slug", "")
        if slug == "starter_project":
            continue
        for action in project.get("next_actions", [])[:3]:
            add_action(
                actions,
                kind="project",
                priority=60,
                title=f"{project.get('title', slug)}：{action}",
                reason="来自项目状态的下一步建议。",
                entrypoint=project.get("dashboard_html") or rel(WORKFLOW_STATE_HTML),
                source=slug,
            )

    if not actions:
        add_action(
            actions,
            kind="continue",
            priority=40,
            title="从今日精读或全局搜索继续推进",
            reason="当前没有阻塞性审计项或到期复习。",
            entrypoint=rel(SEARCH_INDEX_HTML),
        )

    actions.sort(key=lambda item: (-int(item.get("priority", 0)), item.get("kind", ""), item.get("title", "")))
    for index, action in enumerate(actions, start=1):
        action["rank"] = index
    by_kind: dict[str, int] = {}
    for action in actions:
        by_kind[action["kind"]] = by_kind.get(action["kind"], 0) + 1
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source_state": rel(WORKFLOW_STATE_JSON),
        "entrypoint": rel(ACTION_QUEUE_HTML),
        "summary": {
            "total_open": len(actions),
            "high_priority": sum(1 for action in actions if int(action.get("priority", 0)) >= 80),
            "by_kind": by_kind,
        },
        "actions": actions,
    }


def href_for(path: str) -> str:
    if not path:
        return "#"
    if "://" in path or path.startswith("#"):
        return path
    return html.escape(path, quote=True)


def write_action_queue_html(queue: dict[str, Any]) -> None:
    actions = queue.get("actions", [])
    rows = "\n".join(
        f"""        <article class="action task-action">
          <div class="rank">#{action.get("rank", "")}</div>
          <div>
            <h2><a href="{href_for(str(action.get("entrypoint", "")))}">{html.escape(str(action.get("title", "")))}</a></h2>
            <p>{html.escape(str(action.get("reason", "")))}</p>
            <p class="meta">{html.escape(str(action.get("kind", "")))} · priority {action.get("priority", "")} · {html.escape(str(action.get("source", "")))}</p>
          </div>
        </article>"""
        for action in actions
    )
    summary = queue.get("summary", {})
    body = f"""
    <section class="metrics">
      <div class="metric"><b>{summary.get("total_open", 0)}</b><span class="meta">开放行动</span></div>
      <div class="metric"><b>{summary.get("high_priority", 0)}</b><span class="meta">高优先级</span></div>
      <div class="metric"><b>{len(summary.get("by_kind", {}))}</b><span class="meta">行动类型</span></div>
    </section>
    <section class="list">{rows}</section>
"""
    html_text = render_shell(
        title="行动队列",
        subtitle="按优先级排列今天最该处理的事项，先处理高价值学习和阻塞项。",
        current="行动队列",
        body=body,
        output=ACTION_QUEUE_HTML,
        module="今日任务",
        meta=f"Generated {html.escape(str(queue.get('generated_at', '')))}",
        footer="Generated by scripts/build_action_queue.py.",
    )
    write_text_if_changed(ACTION_QUEUE_HTML, html_text)


def write_action_queue(state: dict[str, Any] | None = None) -> tuple[Path, Path]:
    ACTION_QUEUE_JSON.parent.mkdir(parents=True, exist_ok=True)
    queue = build_action_queue(state)
    write_json_if_changed(ACTION_QUEUE_JSON, queue)
    write_action_queue_html(queue)
    return ACTION_QUEUE_JSON, ACTION_QUEUE_HTML
