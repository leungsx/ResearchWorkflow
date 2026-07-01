from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

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
        f"""        <article class="action">
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
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>行动队列</title>
  <style>
    :root {{ --ink:#1e293b; --muted:#64748b; --line:#dbe4ee; --paper:#fff; --soft:#f8fafc; --blue:#2563eb; --green:#16805d; --amber:#a15c07; --ring:rgba(37,99,235,.34); --shadow:0 10px 28px rgba(15,23,42,.06); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:#f8fafc; line-height:1.6; }}
    header {{ background:var(--paper); border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:1120px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:0 0 6px; font-size:18px; }}
    a {{ color:var(--blue); text-decoration:none; text-underline-offset:3px; }}
    a:hover {{ text-decoration:underline; }}
    a:focus-visible {{ outline:3px solid var(--ring); outline-offset:2px; border-radius:7px; }}
    .skip-link {{ position:absolute; left:18px; top:10px; z-index:20; transform:translateY(-140%); background:var(--ink); color:#fff; padding:8px 12px; border-radius:7px; }}
    .skip-link:focus {{ transform:translateY(0); }}
    .sub,.meta {{ color:var(--muted); }}
    .nav {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }}
    .nav a {{ min-height:40px; padding:7px 11px; border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); transition:background-color 160ms ease,border-color 160ms ease,color 160ms ease; }}
    .nav a:hover {{ border-color:#bfcee0; background:#f8fbff; text-decoration:none; }}
    .nav a[aria-current="page"] {{ border-color:#b9ccff; background:#eef4ff; color:#1d4ed8; font-weight:650; }}
    .metrics {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:14px; }}
    .metric,.action {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:var(--shadow); }}
    .metric b {{ display:block; font-size:28px; line-height:1.1; }}
    .list {{ display:grid; gap:10px; }}
    .action {{ display:grid; grid-template-columns:52px 1fr; gap:12px; border-left:4px solid var(--blue); }}
    .rank {{ font-weight:700; color:var(--amber); }}
    @media (max-width:760px) {{ .metrics {{ grid-template-columns:1fr; }} .action {{ grid-template-columns:1fr; }} h1 {{ font-size:28px; }} .wrap {{ padding-left:16px; padding-right:16px; }} .nav {{ flex-wrap:nowrap; overflow-x:auto; padding-bottom:4px; }} .nav a {{ flex:0 0 auto; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ transition-duration:.01ms!important; animation-duration:.01ms!important; animation-iteration-count:1!important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <header>
    <div class="wrap">
      <h1>行动队列</h1>
      <p class="sub">Generated {html.escape(str(queue.get("generated_at", "")))} · 按优先级排列今天最该处理的事项。</p>
      <nav class="nav">
        <a href="action_queue.html" aria-current="page">行动队列</a>
        <a href="workflow_state.html">工作流总状态</a>
        <a href="knowledge_cards/review_today.html">今日复习</a>
        <a href="paper_reading/today.html">今日精读</a>
        <a href="search/index.html">全局搜索</a>
        <a href="workflow_health.html">工作流体检</a>
      </nav>
    </div>
  </header>
  <main class="wrap" id="main-content">
    <section class="metrics">
      <div class="metric"><b>{summary.get("total_open", 0)}</b><span class="meta">开放行动</span></div>
      <div class="metric"><b>{summary.get("high_priority", 0)}</b><span class="meta">高优先级</span></div>
      <div class="metric"><b>{len(summary.get("by_kind", {}))}</b><span class="meta">行动类型</span></div>
    </section>
    <section class="list">{rows}</section>
  </main>
</body>
</html>
"""
    ACTION_QUEUE_HTML.write_text(html_text, encoding="utf-8")


def write_action_queue(state: dict[str, Any] | None = None) -> tuple[Path, Path]:
    ACTION_QUEUE_JSON.parent.mkdir(parents=True, exist_ok=True)
    queue = build_action_queue(state)
    ACTION_QUEUE_JSON.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_action_queue_html(queue)
    return ACTION_QUEUE_JSON, ACTION_QUEUE_HTML
