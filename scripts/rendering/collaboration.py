from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

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
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>项目协作层</title>
  <style>
    :root {{ --ink:#1e293b; --muted:#64748b; --line:#dbe4ee; --paper:#fff; --soft:#f8fafc; --blue:#2563eb; --green:#16805d; --amber:#a15c07; --ring:rgba(37,99,235,.34); --shadow:0 10px 28px rgba(15,23,42,.06); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:#f8fafc; line-height:1.6; }}
    header {{ background:var(--paper); border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:1160px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:0 0 8px; font-size:20px; }}
    h3 {{ margin:0 0 8px; font-size:15px; }}
    a {{ color:var(--blue); text-decoration:none; text-underline-offset:3px; }}
    a:hover {{ text-decoration:underline; }}
    a:focus-visible {{ outline:3px solid var(--ring); outline-offset:2px; border-radius:7px; }}
    .skip-link {{ position:absolute; left:18px; top:10px; z-index:20; transform:translateY(-140%); background:var(--ink); color:#fff; padding:8px 12px; border-radius:7px; }}
    .skip-link:focus {{ transform:translateY(0); }}
    .sub,.meta {{ color:var(--muted); }}
    .nav,.links {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
    .nav a,.links a {{ min-height:40px; padding:7px 11px; border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); transition:background-color 160ms ease,border-color 160ms ease,color 160ms ease; }}
    .nav a:hover,.links a:hover {{ border-color:#bfcee0; background:#f8fbff; text-decoration:none; }}
    .nav a[aria-current="page"] {{ border-color:#b9ccff; background:#eef4ff; color:#1d4ed8; font-weight:650; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:14px; }}
    .metric,.project,.panel {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:var(--shadow); }}
    .metric b {{ display:block; font-size:28px; line-height:1.1; }}
    .list {{ display:grid; gap:12px; }}
    .project {{ border-left:4px solid var(--green); }}
    .columns {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:12px; }}
    ul {{ margin:0; padding-left:20px; }}
    li {{ margin:5px 0; }}
    @media (max-width:820px) {{ .metrics,.columns {{ grid-template-columns:1fr; }} h1 {{ font-size:28px; }} .wrap {{ padding-left:16px; padding-right:16px; }} .nav,.links {{ flex-wrap:nowrap; overflow-x:auto; padding-bottom:4px; }} .nav a,.links a {{ flex:0 0 auto; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ transition-duration:.01ms!important; animation-duration:.01ms!important; animation-iteration-count:1!important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <header>
    <div class="wrap">
      <h1>项目协作层</h1>
      <p class="sub">Generated {html.escape(str(state.get("generated_at", "")))} · 把用户决策、Codex 可执行事项和项目入口放在同一页。</p>
      <nav class="nav">
        <a href="project_collaboration.html" aria-current="page">项目协作层</a>
        <a href="workflow_state.html">工作流总状态</a>
        <a href="action_queue.html">行动队列</a>
        <a href="search/index.html">全局搜索</a>
        <a href="knowledge_cards/review_today.html">今日复习</a>
        <a href="workflow_health.html">工作流体检</a>
      </nav>
    </div>
  </header>
  <main class="wrap" id="main-content">
    <section class="metrics">
      <div class="metric"><b>{summary.get("project_count", 0)}</b><span class="meta">项目</span></div>
      <div class="metric"><b>{summary.get("user_waiting", 0)}</b><span class="meta">用户待确认</span></div>
      <div class="metric"><b>{summary.get("codex_ready", 0)}</b><span class="meta">Codex 可推进</span></div>
      <div class="metric"><b>{summary.get("open_actions", 0)}</b><span class="meta">行动队列</span></div>
    </section>
    <section class="list">{cards or '<div class="panel">暂无项目状态。</div>'}</section>
  </main>
</body>
</html>
"""
    COLLABORATION_HTML.write_text(html_text, encoding="utf-8")


def write_collaboration_state() -> tuple[Path, Path]:
    COLLABORATION_JSON.parent.mkdir(parents=True, exist_ok=True)
    state = build_collaboration_state()
    COLLABORATION_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_collaboration_html(state)
    return COLLABORATION_JSON, COLLABORATION_HTML
