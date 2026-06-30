from __future__ import annotations

import datetime as dt
import html
import json
import subprocess
from pathlib import Path
from typing import Any

from rendering.paths import (
    ARTIFACT_MANIFEST,
    ACTION_QUEUE_HTML,
    ACTION_QUEUE_JSON,
    BACKUP_INDEX,
    GRAPH_DIR,
    KNOWLEDGE_GRAPH,
    PAPER_READING,
    PROJECTS,
    REVIEW_STATE,
    REVIEW_TODAY,
    ROOT,
    SEARCH_INDEX_HTML,
    SEARCH_INDEX_JSON,
    WORKFLOW_AUDIT_JSON,
    WORKFLOW_HEALTH,
    WORKFLOW_STATE_HTML,
    WORKFLOW_STATE_JSON,
    csv_rows,
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


def latest_file(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern), key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
    return files[0] if files else None


def git_dirty_count() -> int:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return -1
    return len([line for line in result.stdout.splitlines() if line.strip()])


def graph_summary() -> dict[str, Any]:
    nodes = csv_rows(GRAPH_DIR / "obsidian_nodes.csv")
    edges = csv_rows(GRAPH_DIR / "obsidian_edges.csv")
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "html": rel(KNOWLEDGE_GRAPH / "index.html"),
    }


def project_summaries() -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for project in sorted(PROJECTS.glob("*/project_state.json")):
        payload = read_json(project, {})
        project_meta = payload.get("project", {}) if isinstance(payload, dict) else {}
        literature = payload.get("literature", {}) if isinstance(payload, dict) else {}
        review = payload.get("review", {}) if isinstance(payload, dict) else {}
        artifacts = payload.get("artifacts", {}) if isinstance(payload, dict) else {}
        dashboard_html = ""
        for entry in artifacts.get("html_entries", []) if isinstance(artifacts, dict) else []:
            source_path = str(entry.get("source_path", ""))
            display_path = str(entry.get("display_path", ""))
            if source_path.endswith("00_project_dashboard.md") and display_path.endswith(".html"):
                dashboard_html = display_path
                break
        projects.append(
            {
                "slug": project.parent.name,
                "title": project_meta.get("title", project.parent.name),
                "status": project_meta.get("status", ""),
                "matrix_rows": literature.get("matrix_rows", 0),
                "reader_packages": literature.get("reader_packages", 0),
                "latest_deep_read": literature.get("latest_deep_read", {}),
                "next_reading_candidates": literature.get("next_reading_candidates", [])[:3],
                "review_due_count": review.get("due_count", 0),
                "next_actions": payload.get("next_actions", [])[:4] if isinstance(payload, dict) else [],
                "state_path": rel(project),
                "dashboard_html": dashboard_html,
            }
        )
    return projects


def build_workflow_state(audit_checks: list[Any] | None = None) -> dict[str, Any]:
    manifest_rows = csv_rows(ARTIFACT_MANIFEST)
    search = read_json(SEARCH_INDEX_JSON, {"entry_count": 0, "entries": []})
    review = read_json(REVIEW_STATE, {"summary": {}, "focus_items": []})
    latest_backup = latest_file(ROOT / "backups", "*.zip")
    checks = []
    if audit_checks:
        for check in audit_checks:
            checks.append(
                {
                    "area": getattr(check, "area", ""),
                    "status": getattr(check, "status", ""),
                    "title": getattr(check, "title", ""),
                    "detail": getattr(check, "detail", ""),
                }
            )
    audit_counts = {
        "PASS": sum(1 for check in checks if check.get("status") == "PASS"),
        "WARN": sum(1 for check in checks if check.get("status") == "WARN"),
        "FAIL": sum(1 for check in checks if check.get("status") == "FAIL"),
    }
    review_summary = review.get("summary", {}) if isinstance(review, dict) else {}
    projects = project_summaries()
    next_actions: list[str] = []
    if review_summary.get("due_count", 0):
        next_actions.append(f"先处理 {review_summary.get('due_count')} 个到期复习项。")
    for project in projects:
        next_actions.extend(project.get("next_actions", [])[:2])
    if audit_counts["FAIL"]:
        next_actions.insert(0, "先修复 workflow-audit 的 FAIL 项。")
    elif audit_counts["WARN"]:
        next_actions.append("择机处理 workflow-audit 的 WARN 项，尤其是 Git 快照和到期复习。")
    if not next_actions:
        next_actions.append("从今日精读入口或全局搜索入口继续推进阅读。")

    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "entrypoints": {
            "study_dashboard": "study_dashboard.html",
            "today": rel(PAPER_READING / "today.html"),
            "review_today": rel(REVIEW_TODAY),
            "knowledge_graph": rel(KNOWLEDGE_GRAPH / "index.html"),
            "search": rel(SEARCH_INDEX_HTML),
            "workflow_health": rel(WORKFLOW_HEALTH),
            "workflow_state": rel(WORKFLOW_STATE_HTML),
            "action_queue": rel(ACTION_QUEUE_HTML),
        },
        "counts": {
            "manifest_rows": len(manifest_rows),
            "search_entries": search.get("entry_count", 0) if isinstance(search, dict) else 0,
            "project_count": len(projects),
            "git_dirty_paths": git_dirty_count(),
        },
        "audit": {
            "counts": audit_counts,
            "checks": checks,
            "health_html": rel(WORKFLOW_HEALTH),
            "report_json": rel(WORKFLOW_AUDIT_JSON),
        },
        "review": {
            "summary": review_summary,
            "focus_items": review.get("focus_items", [])[:8] if isinstance(review, dict) else [],
            "state_path": rel(REVIEW_STATE),
            "html": rel(REVIEW_TODAY),
        },
        "graph": graph_summary(),
        "projects": projects,
        "artifacts": {
            "manifest": rel(ARTIFACT_MANIFEST),
            "search_index": rel(SEARCH_INDEX_JSON),
            "backup_index": rel(BACKUP_INDEX) if BACKUP_INDEX.exists() else "",
            "latest_backup": rel(latest_backup) if latest_backup else "",
            "action_queue": rel(ACTION_QUEUE_JSON),
            "workflow_audit_report": rel(WORKFLOW_AUDIT_JSON),
        },
        "next_actions": list(dict.fromkeys(next_actions))[:8],
    }


def status_class(status: str) -> str:
    return status.lower() if status in {"PASS", "WARN", "FAIL"} else "warn"


def write_workflow_state_html(state: dict[str, Any]) -> None:
    counts = state.get("counts", {})
    audit = state.get("audit", {}).get("counts", {})
    review_summary = state.get("review", {}).get("summary", {})
    projects = state.get("projects", [])
    next_actions = state.get("next_actions", [])
    project_cards = "\n".join(
        f"""
        <article class="item">
          <h2>{html.escape(str(project.get("title", "")))}</h2>
          <p class="meta">{html.escape(str(project.get("slug", "")))} · 文献 {project.get("matrix_rows", 0)} · Reader {project.get("reader_packages", 0)}</p>
          <ul>{''.join(f'<li>{html.escape(str(action))}</li>' for action in project.get('next_actions', [])[:3])}</ul>
        </article>
        """
        for project in projects
    )
    action_items = "".join(f"<li>{html.escape(str(action))}</li>" for action in next_actions)
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>工作流总状态</title>
  <style>
    :root {{ --ink:#182026; --muted:#61707d; --line:#d9e0e6; --paper:#fff; --soft:#f6f8fa; --blue:#2463eb; --green:#16805d; --amber:#a15c07; --rose:#b4234b; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:#f4f6f8; line-height:1.55; }}
    header {{ background:var(--paper); border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:1160px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:0 0 10px; font-size:18px; }}
    a {{ color:var(--blue); text-decoration:none; }}
    .sub,.meta {{ color:var(--muted); }}
    .nav {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }}
    .nav a {{ min-height:34px; padding:6px 10px; border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); }}
    .grid {{ display:grid; grid-template-columns:repeat(12,1fr); gap:14px; }}
    .metric,.panel,.item {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .metric {{ grid-column:span 3; }}
    .metric b {{ display:block; font-size:28px; line-height:1.1; }}
    .panel {{ grid-column:span 6; }}
    .panel.wide {{ grid-column:1/-1; }}
    .list {{ display:grid; gap:10px; }}
    .item {{ border-left:3px solid var(--blue); background:var(--soft); }}
    .status {{ display:inline-flex; border-radius:999px; padding:2px 8px; background:#eef3f8; color:var(--muted); font-size:12px; }}
    .pass {{ color:var(--green); }} .warn {{ color:var(--amber); }} .fail {{ color:var(--rose); }}
    @media (max-width:840px) {{ .metric,.panel {{ grid-column:1/-1; }} h1 {{ font-size:28px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>工作流总状态</h1>
      <p class="sub">Generated {html.escape(str(state.get("generated_at", "")))} · 聚合项目、复习、搜索、图谱和审计状态。</p>
      <nav class="nav">
        <a href="study_dashboard.html">总览</a>
        <a href="paper_reading/today.html">今日精读</a>
        <a href="knowledge_cards/review_today.html">今日复习</a>
        <a href="search/index.html">全局搜索</a>
        <a href="knowledge_graph/index.html">知识图谱</a>
        <a href="action_queue.html">行动队列</a>
        <a href="workflow_health.html">工作流体检</a>
      </nav>
    </div>
  </header>
  <main class="wrap">
    <section class="grid">
      <div class="metric"><b>{counts.get("manifest_rows", 0)}</b><span class="meta">manifest 条目</span></div>
      <div class="metric"><b>{counts.get("search_entries", 0)}</b><span class="meta">搜索条目</span></div>
      <div class="metric"><b>{review_summary.get("due_count", 0)}</b><span class="meta">到期复习</span></div>
      <div class="metric"><b>{audit.get("FAIL", 0)}/{audit.get("WARN", 0)}</b><span class="meta">FAIL/WARN</span></div>

      <section class="panel wide">
        <h2>下一步</h2>
        <ol>{action_items}</ol>
      </section>
      <section class="panel">
        <h2>核心入口</h2>
        <div class="list">
          <div class="item"><a href="paper_reading/today.html">今日精读入口</a><div class="meta">每天主读论文。</div></div>
          <div class="item"><a href="knowledge_cards/review_today.html">今日复习入口</a><div class="meta">主动回忆到期知识卡。</div></div>
          <div class="item"><a href="action_queue.html">行动队列</a><div class="meta">按优先级处理今天最该做的事。</div></div>
          <div class="item"><a href="search/index.html">全局搜索入口</a><div class="meta">查论文、概念、方法和项目材料。</div></div>
        </div>
      </section>
      <section class="panel">
        <h2>审计状态</h2>
        <p><span class="status pass">PASS {audit.get("PASS", 0)}</span> <span class="status warn">WARN {audit.get("WARN", 0)}</span> <span class="status fail">FAIL {audit.get("FAIL", 0)}</span></p>
        <p class="meta"><a href="workflow_health.html">打开工作流体检页</a></p>
      </section>
      <section class="panel wide">
        <h2>项目状态</h2>
        <div class="list">{project_cards or '<div class="item">暂无项目状态。</div>'}</div>
      </section>
    </section>
  </main>
</body>
</html>
"""
    WORKFLOW_STATE_HTML.write_text(html_text, encoding="utf-8")


def write_workflow_state(audit_checks: list[Any] | None = None) -> tuple[Path, Path]:
    WORKFLOW_STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    state = build_workflow_state(audit_checks)
    WORKFLOW_STATE_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_workflow_state_html(state)
    return WORKFLOW_STATE_JSON, WORKFLOW_STATE_HTML
