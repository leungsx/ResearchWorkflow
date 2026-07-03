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
from rendering.ui import render_guidance, render_shell
from rendering.workflow_state import build_workflow_state, read_json, rel


ACTION_KIND_LABELS = {
    "audit_fail": "审计失败",
    "audit_warn": "系统提醒",
    "review": "复习任务",
    "review_item": "知识卡复习",
    "project": "项目推进",
    "continue": "继续推进",
}

PRIORITY_BAND_LABELS = {
    "P0": "P0 阻塞写作/投稿",
    "P1": "P1 今日学习/阅读",
    "P2": "P2 项目成熟度",
    "P3": "P3 系统维护",
}

PRIORITY_BAND_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def action_id(kind: str, title: str, index: int) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in title)[:42].strip("-")
    return f"{kind}-{index + 1}-{safe or 'item'}"


def classify_action(kind: str, title: str, reason: str, source: str) -> tuple[str, str]:
    text = f"{title} {reason} {source}"
    if kind == "audit_fail" or any(term in text for term in ["ERROR", "FAIL", "投稿", "正文", "证据门禁", "evidence gate"]):
        return "P0", "阻塞写作、引用或投稿前审查，必须先处理。"
    if kind in {"review", "review_item", "continue"}:
        return "P1", "今天应完成的学习、阅读或主动回忆任务。"
    if kind == "project":
        return "P2", "推进主项目成熟度，但通常不阻塞当天启动。"
    return "P3", "系统维护或提醒，除非失败，否则放在学习和项目任务之后。"


def priority_for_band(band: str, kind: str) -> int:
    base = {"P0": 100, "P1": 80, "P2": 60, "P3": 30}.get(band, 30)
    boost = {
        "audit_fail": 0,
        "review": 10,
        "review_item": 0,
        "project": 0,
        "audit_warn": 0,
        "continue": 5,
    }.get(kind, 0)
    return base + boost


def add_action(actions: list[dict[str, Any]], *, kind: str, title: str, reason: str, entrypoint: str, source: str = "") -> None:
    priority_band, priority_reason = classify_action(kind, title, reason, source)
    actions.append(
        {
            "id": action_id(kind, title, len(actions)),
            "kind": kind,
            "priority": priority_for_band(priority_band, kind),
            "priority_band": priority_band,
            "priority_label": PRIORITY_BAND_LABELS[priority_band],
            "priority_reason": priority_reason,
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
                title=f"修复审计失败：{check.get('title', '')}",
                reason=check.get("detail", ""),
                entrypoint=rel(WORKFLOW_HEALTH),
                source=check.get("area", ""),
            )
        elif status == "WARN" and check.get("area") in {"复习队列", "Git/异地备份", "备份"}:
            add_action(
                actions,
                kind="audit_warn",
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
            title=f"完成 {review_summary.get('due_count')} 个到期知识卡复习",
            reason="先主动回忆，再打开知识卡核对概念、误区和研究用法。",
            entrypoint=rel(REVIEW_TODAY),
            source=review.get("state_path", ""),
        )
        for item in focus_items[:5]:
            add_action(
                actions,
                kind="review_item",
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
                title=f"{project.get('title', slug)}：{action}",
                reason="来自项目状态的下一步建议。",
                entrypoint=project.get("dashboard_html") or rel(WORKFLOW_STATE_HTML),
                source=slug,
            )

    if not actions:
        add_action(
            actions,
            kind="continue",
            title="从今日精读或全局搜索继续推进",
            reason="当前没有阻塞性审计项或到期复习。",
            entrypoint=rel(SEARCH_INDEX_HTML),
        )

    actions.sort(
        key=lambda item: (
            PRIORITY_BAND_ORDER.get(str(item.get("priority_band", "P3")), 9),
            -int(item.get("priority", 0)),
            item.get("kind", ""),
            item.get("title", ""),
        )
    )
    for index, action in enumerate(actions, start=1):
        action["rank"] = index
    by_kind: dict[str, int] = {}
    by_priority_band: dict[str, int] = {}
    for action in actions:
        by_kind[action["kind"]] = by_kind.get(action["kind"], 0) + 1
        band = str(action.get("priority_band", "P3"))
        by_priority_band[band] = by_priority_band.get(band, 0) + 1
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source_state": rel(WORKFLOW_STATE_JSON),
        "entrypoint": rel(ACTION_QUEUE_HTML),
        "summary": {
            "total_open": len(actions),
            "high_priority": sum(1 for action in actions if action.get("priority_band") in {"P0", "P1"}),
            "by_kind": by_kind,
            "by_priority_band": by_priority_band,
        },
        "actions": actions,
    }


def href_for(path: str) -> str:
    if not path:
        return "#"
    if "://" in path or path.startswith("#"):
        return path
    return html.escape(path, quote=True)


def action_kind_label(kind: object) -> str:
    return ACTION_KIND_LABELS.get(str(kind), str(kind))


def copy_command_for_action(action: dict[str, Any]) -> str:
    kind = str(action.get("kind", ""))
    source = str(action.get("source", ""))
    entrypoint = str(action.get("entrypoint", "action_queue.html")) or "action_queue.html"
    if kind.startswith("audit"):
        return "make workflow-audit-readonly"
    if kind in {"review", "review_item"}:
        return "make review-server-ensure"
    if kind == "project" and source:
        return f"make project-state PROJECT={source}"
    return f"open {entrypoint}"


def next_step_for_action(action: dict[str, Any]) -> str:
    kind = str(action.get("kind", ""))
    if kind == "review":
        return "完成后：继续今日精读，或进入核页码补齐写作证据。"
    if kind == "review_item":
        return "完成后：回到今日复习，继续下一张知识卡。"
    if kind.startswith("audit"):
        return "完成后：重新运行系统体检，确认提醒是否消失。"
    if kind == "project":
        return "完成后：打开写论文或找证据，把结果沉淀到项目工作台。"
    return "完成后：回到今日工作台选择下一项。"


def copy_button(command: str) -> str:
    escaped = html.escape(command, quote=True)
    return f'<button class="inline-button" type="button" data-copy="{escaped}" data-label="复制命令">复制命令</button><span class="copy-feedback" aria-live="polite"></span>'


def write_action_queue_html(queue: dict[str, Any]) -> None:
    actions = queue.get("actions", [])
    primary = actions[0] if actions else {}
    primary_entry = str(primary.get("entrypoint", "paper_reading/today.html"))
    primary_command = copy_command_for_action(primary) if primary else "make daily"
    primary_html = f"""
    <section class="panel wide cta-card">
      <div class="cta-layout">
        <div>
          <p class="eyebrow">今日主任务</p>
          <h2 class="cta-title"><a href="{href_for(primary_entry)}">{html.escape(str(primary.get("title", "从今日精读继续推进")))}</a></h2>
          <p>{html.escape(str(primary.get("reason", "当前没有阻塞项；优先继续阅读、复习或核验证据。")))}</p>
          <p class="meta">{html.escape(next_step_for_action(primary) if primary else "完成后：回到今日工作台选择下一项。")}</p>
        </div>
        <div class="command-stack">
          <a class="inline-button primary" href="{href_for(primary_entry)}">打开入口</a>
          {copy_button(primary_command)}
          <code>{html.escape(primary_command)}</code>
        </div>
      </div>
    </section>
"""
    rows = "\n".join(
        f"""        <article class="action task-action">
          <div class="rank">#{action.get("rank", "")}</div>
          <div>
            <h2><a href="{href_for(str(action.get("entrypoint", "")))}">{html.escape(str(action.get("title", "")))}</a></h2>
            <p>{html.escape(str(action.get("reason", "")))}</p>
            <p class="meta">{html.escape(str(action.get("priority_label", "")))} · {html.escape(action_kind_label(action.get("kind", "")))} · 来源 {html.escape(str(action.get("source", "") or "系统生成"))}</p>
            <p class="meta">{html.escape(str(action.get("priority_reason", "")))}</p>
          </div>
        </article>"""
        for action in actions
    )
    summary = queue.get("summary", {})
    body = f"""
    {primary_html}
    {render_guidance(
        purpose="把审计提醒、到期复习和项目推进任务按优先级排成今天的处理顺序。",
        first="先完成今日主任务；不要从系统维护项开始，除非它是 FAIL 或阻塞写作。",
        after="完成一项后回到今日工作台，或运行 make daily 让任务队列重新排序。",
        output=ACTION_QUEUE_HTML,
        command="make daily",
        action_label="打开今日工作台",
        action_target=ROOT / "study_dashboard.html",
    )}
    <section class="metrics">
      <div class="metric"><b>{summary.get("total_open", 0)}</b><span class="meta">开放行动</span></div>
      <div class="metric"><b>{summary.get("high_priority", 0)}</b><span class="meta">P0/P1 任务</span></div>
      <div class="metric"><b>{len(summary.get("by_kind", {}))}</b><span class="meta">行动类型</span></div>
      <div class="metric"><b>{len(summary.get("by_priority_band", {}))}</b><span class="meta">优先级层级</span></div>
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
