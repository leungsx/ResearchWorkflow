from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

from rendering.io import write_json_if_changed, write_text_if_changed
from rendering.paths import (
    ACTION_QUEUE_JSON,
    COLLABORATION_HTML,
    COLLABORATION_JSON,
    PROJECTS,
    REVIEW_TODAY,
    ARCHIVE_POLICY_HTML,
    ROOT,
    SEARCH_INDEX_HTML,
    WORKFLOW_HEALTH,
    WORKFLOW_STATE_HTML,
)
from rendering.ui import render_guidance, render_shell


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    item = Path(path)
    try:
        return str(item.relative_to(ROOT))
    except ValueError:
        return str(item)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def project_stage(project_state: dict[str, Any]) -> str:
    literature = project_state.get("literature", {})
    matrix_rows = int(literature.get("matrix_rows", 0) or 0)
    readers = int(literature.get("reader_packages", 0) or 0)
    latest_deep = literature.get("latest_deep_read", {})
    if not matrix_rows:
        return "setup"
    if readers < 3:
        return "source_building"
    if latest_deep:
        return "synthesis"
    return "reading"


def user_handoffs(project_state: dict[str, Any]) -> list[str]:
    handoffs: list[str] = []
    evidence = project_state.get("evidence_gate", {})
    literature = project_state.get("literature", {})
    if evidence.get("status") and str(evidence.get("status")).upper() != "PASS":
        handoffs.append("人工确认 evidence gate 中 WARN/ERROR 的证据边界。")
    candidates = literature.get("next_reading_candidates", []) if isinstance(literature, dict) else []
    if any(not item.get("pdf_path") for item in candidates):
        handoffs.append("如要读取 metadata-only 文献，需要先补 PDF/CAJ 或授权下载。")
    review = project_state.get("review", {})
    if review.get("due_count", 0):
        handoffs.append(f"完成 {review.get('due_count')} 个到期知识卡主动回忆。")
    return handoffs[:4]


def codex_handoffs(project_state: dict[str, Any]) -> list[str]:
    actions = list(project_state.get("next_actions", [])[:4])
    if not actions:
        actions.append("刷新项目状态、搜索索引和工作流体检。")
    actions.append("把下一篇精读结果沉淀为 HTML、知识卡、图谱关系和复习问题。")
    return list(dict.fromkeys(actions))[:5]


def project_entrypoints(project_state: dict[str, Any]) -> dict[str, str]:
    entrypoints = project_state.get("entrypoints", {}) if isinstance(project_state, dict) else {}
    return {
        "dashboard": entrypoints.get("project_dashboard", ""),
        "reading_board": entrypoints.get("reading_board", ""),
        "literature_workbench": entrypoints.get("literature_workbench", ""),
        "literature_synthesis": entrypoints.get("literature_synthesis", ""),
        "incoming_pdf_triage": entrypoints.get("incoming_pdf_triage", ""),
        "evidence_locator_table": entrypoints.get("evidence_locator_table", ""),
        "manuscript_writing_panel": entrypoints.get("manuscript_writing_panel", ""),
        "review_today": entrypoints.get("review_today", rel(REVIEW_TODAY)),
        "search": entrypoints.get("search", rel(SEARCH_INDEX_HTML)),
        "archive_policy": entrypoints.get("archive_policy", rel(ARCHIVE_POLICY_HTML)),
    }


def project_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for state_path in sorted(PROJECTS.glob("*/project_state.json")):
        state = read_json(state_path, {})
        if not isinstance(state, dict):
            continue
        project = state.get("project", {})
        literature = state.get("literature", {})
        review = state.get("review", {})
        artifacts = state.get("artifacts", {})
        items.append(
            {
                "slug": project.get("slug", state_path.parent.name),
                "title": project.get("title", state_path.parent.name),
                "status": project.get("status", ""),
                "stage": project_stage(state),
                "state_path": rel(state_path),
                "matrix_rows": literature.get("matrix_rows", 0),
                "reader_packages": literature.get("reader_packages", 0),
                "review_due": review.get("due_count", 0),
                "latest_deep_read": literature.get("latest_deep_read", {}),
                "entrypoints": project_entrypoints(state),
                "user_handoffs": user_handoffs(state),
                "codex_handoffs": codex_handoffs(state),
                "source_documents": state.get("source_documents", {}),
                "artifact_count": artifacts.get("project_related_entries", 0),
            }
        )
    return items


def build_collaboration_state() -> dict[str, Any]:
    projects = project_items()
    action_queue = read_json(ACTION_QUEUE_JSON, {"summary": {}, "actions": []})
    action_summary = action_queue.get("summary", {}) if isinstance(action_queue, dict) else {}
    user_waiting = sum(len(project.get("user_handoffs", [])) for project in projects)
    codex_ready = sum(len(project.get("codex_handoffs", [])) for project in projects)
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "entrypoint": rel(COLLABORATION_HTML),
        "summary": {
            "project_count": len(projects),
            "user_waiting": user_waiting,
            "codex_ready": codex_ready,
            "open_actions": action_summary.get("total_open", 0),
        },
        "roles": {
            "user": [
                "确认研究方向、证据边界和是否补全文。",
                "完成主动回忆和主观判断。",
                "决定哪些研究问题进入写作或实验设计。",
            ],
            "codex": [
                "刷新状态、索引、HTML 入口和审计报告。",
                "把论文转成知识卡、图谱关系和项目行动。",
                "根据项目状态推荐下一篇可精读文献。",
            ],
        },
        "entrypoints": {
            "workflow_state": rel(WORKFLOW_STATE_HTML),
            "action_queue": action_queue.get("entrypoint", "action_queue.html") if isinstance(action_queue, dict) else "action_queue.html",
            "review_today": rel(REVIEW_TODAY),
            "search": rel(SEARCH_INDEX_HTML),
            "workflow_health": rel(WORKFLOW_HEALTH),
        },
        "projects": projects,
    }


def href_for(path: str) -> str:
    return html.escape(path or "#", quote=True)


def write_collaboration_html(state: dict[str, Any]) -> None:
    summary = state.get("summary", {})
    projects = state.get("projects", [])
    cards = "\n".join(
        f"""
        <article class="project">
          <h2>{html.escape(str(project.get("title", "")))}</h2>
          <p class="meta">{html.escape(str(project.get("slug", "")))} · {html.escape(str(project.get("stage", "")))} · 文献 {project.get("matrix_rows", 0)} · Reader {project.get("reader_packages", 0)}</p>
          <div class="columns">
            <section>
              <h3>用户待确认</h3>
              <ul>{''.join(f'<li>{html.escape(str(item))}</li>' for item in project.get('user_handoffs', []) or ['暂无必须人工决策。'])}</ul>
            </section>
            <section>
              <h3>Codex 可推进</h3>
              <ul>{''.join(f'<li>{html.escape(str(item))}</li>' for item in project.get('codex_handoffs', []) or ['刷新项目状态。'])}</ul>
            </section>
          </div>
          <div class="links">
            {''.join(f'<a href="{href_for(str(value))}">{html.escape(str(key))}</a>' for key, value in project.get('entrypoints', {}).items() if value)}
          </div>
        </article>
        """
        for project in projects
    )
    body = f"""
    {render_guidance(
        purpose="把需要你人工判断的事项和 Codex 可以继续推进的事项分开，避免系统把主观决策自动执行。",
        first="先处理“用户待确认”；没有人工阻塞时，再让 Codex 推进下一篇阅读、证据或写作任务。",
        after="确认完决策后回到行动队列，让任务排序重新选择今日主任务。",
        output=COLLABORATION_HTML,
        command="make collaboration-state",
        action_label="打开行动队列",
        action_target=ROOT / "action_queue.html",
    )}
    <section class="metrics">
      <div class="metric"><b>{summary.get("project_count", 0)}</b><span class="meta">项目</span></div>
      <div class="metric"><b>{summary.get("user_waiting", 0)}</b><span class="meta">用户待确认</span></div>
      <div class="metric"><b>{summary.get("codex_ready", 0)}</b><span class="meta">Codex 可推进</span></div>
      <div class="metric"><b>{summary.get("open_actions", 0)}</b><span class="meta">行动队列</span></div>
    </section>
    <section class="list">{cards or '<div class="panel">暂无项目状态。</div>'}</section>
"""
    html_text = render_shell(
        title="待我确认",
        subtitle="集中查看需要你判断的事项、Codex 可继续推进的任务和项目入口。",
        current="待我确认",
        body=body,
        output=COLLABORATION_HTML,
        module="系统",
        meta=f"Generated {html.escape(str(state.get('generated_at', '')))}",
        footer="Generated by scripts/build_collaboration_state.py.",
    )
    write_text_if_changed(COLLABORATION_HTML, html_text)


def write_collaboration_state() -> tuple[Path, Path]:
    COLLABORATION_JSON.parent.mkdir(parents=True, exist_ok=True)
    state = build_collaboration_state()
    write_json_if_changed(COLLABORATION_JSON, state)
    write_collaboration_html(state)
    return COLLABORATION_JSON, COLLABORATION_HTML
