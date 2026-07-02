#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from rendering.io import write_text_if_changed
from rendering.manifest import artifact_manifest_rows, build_artifact_manifest
from rendering.paths import (
    ARTIFACT_MANIFEST,
    ACTION_QUEUE_HTML,
    ACTION_QUEUE_JSON,
    ARCHIVE_POLICY_HTML,
    BACKUP_INDEX,
    COLLABORATION_HTML,
    CONCEPTS,
    DIR_VIEWS,
    GRAPH_DIR,
    HTML_LOGS,
    KNOWLEDGE_CARD_VIEWS,
    KNOWLEDGE_CARDS,
    KNOWLEDGE_GRAPH,
    LEARNING_SESSIONS,
    LOG_VIEWS,
    METHODS,
    PAPER_READING,
    PAPER_VIEWS,
    REVIEW_QUEUE,
    REVIEW_STATE,
    REVIEW_TODAY,
    ROOT,
    SEARCH_INDEX_HTML,
    SEARCH_INDEX_JSON,
    VAULT,
    WORKFLOW_HEALTH,
    WORKFLOW_STATE_HTML,
    csv_rows,
    esc,
    href,
    html_title,
    latest_file,
    list_html,
    list_md,
    md_title,
    paper_pages,
)
from rendering.archive_policy import write_archive_policy
from rendering.collaboration import write_collaboration_state
from rendering.routes import (
    card_view_path,
    directory_sources_from_markdown,
    directory_view_path,
    display_href,
    display_link_target,
    html_view_for_local_path,
    local_markdown_source,
    log_view_path,
    markdown_sources_from_paper_pages,
    paper_markdown_view_path,
    paper_markdown_view_subtitle,
    paper_markdown_view_title,
    relative_label,
)
from rendering.review import build_review_state as build_review_state_payload
from rendering.review import write_review_state
from rendering.search import build_search_index, write_search_index
from workflow_config import active_project_slug


ACTIVE_PROJECT = active_project_slug()


def active_project_path(*parts: str) -> Path:
    return ROOT / "projects" / ACTIVE_PROJECT / Path(*parts)


def read_json(path: Path, default: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def due_reviews() -> list[dict[str, str]]:
    return build_review_state_payload()["due_items"]


def graph_counts() -> tuple[int, int, list[tuple[str, int]]]:
    nodes = csv_rows(GRAPH_DIR / "obsidian_nodes.csv")
    edges = csv_rows(GRAPH_DIR / "obsidian_edges.csv")
    counter: Counter[str] = Counter()
    for row in edges:
        if row.get("Source"):
            counter[row["Source"]] += 1
        if row.get("Target"):
            counter[row["Target"]] += 1
    return len(nodes), len(edges), counter.most_common(10)


def common_css() -> str:
    return """
    :root {
      color-scheme: light;
      --ink: #1e293b;
      --muted: #64748b;
      --line: #dbe4ee;
      --paper: #ffffff;
      --soft: #f8fafc;
      --blue: #2563eb;
      --green: #16805d;
      --amber: #a15c07;
      --rose: #b4234b;
      --ring: rgba(37, 99, 235, 0.34);
      --shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", Arial, sans-serif;
      color: var(--ink);
      background: #f8fafc;
      line-height: 1.6;
    }
    header {
      background: var(--paper);
      border-bottom: 1px solid var(--line);
    }
    .wrap { max-width: 1160px; margin: 0 auto; padding: 28px 22px; }
    h1 { margin: 0 0 8px; font-size: 34px; line-height: 1.18; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 20px; letter-spacing: 0; }
    h3 { margin: 0 0 8px; font-size: 16px; letter-spacing: 0; }
    p { margin: 0 0 12px; }
    a { color: var(--blue); text-decoration: none; text-underline-offset: 3px; }
    a:hover { text-decoration: underline; }
    a:focus-visible,
    button:focus-visible,
    select:focus-visible,
    input:focus-visible {
      outline: 3px solid var(--ring);
      outline-offset: 2px;
      border-radius: 7px;
    }
    .skip-link {
      position: absolute;
      left: 18px;
      top: 10px;
      z-index: 20;
      transform: translateY(-140%);
      background: var(--ink);
      color: #fff;
      padding: 8px 12px;
      border-radius: 7px;
    }
    .skip-link:focus { transform: translateY(0); }
    .sub { color: var(--muted); max-width: 780px; }
    .nav { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
    .nav a {
      display: inline-flex;
      align-items: center;
      min-height: 44px;
      padding: 7px 11px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font-size: 14px;
      transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease, box-shadow 160ms ease;
    }
    .nav a:hover {
      border-color: #bfcee0;
      background: #f8fbff;
      text-decoration: none;
    }
    .nav a[aria-current="page"] {
      border-color: #b9ccff;
      background: #eef4ff;
      color: #1d4ed8;
      font-weight: 650;
    }
    main.wrap { padding-top: 22px; }
    .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 14px; }
    .panel {
      grid-column: span 6;
      min-width: 0;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: var(--shadow);
    }
    .panel.wide { grid-column: 1 / -1; }
    .metric {
      grid-column: span 3;
      min-width: 0;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--shadow);
    }
    .metric b { display: block; font-size: 28px; line-height: 1.1; }
    .metric span { color: var(--muted); font-size: 13px; }
    .list { display: grid; gap: 10px; min-width: 0; }
    .item {
      min-width: 0;
      border-left: 3px solid var(--blue);
      background: var(--soft);
      padding: 10px 12px;
      border-radius: 0 7px 7px 0;
      transition: background-color 160ms ease, border-color 160ms ease, transform 160ms ease;
    }
    .item:hover {
      background: #eef4ff;
      transform: translateY(-1px);
    }
    .item.green { border-left-color: var(--green); }
    .item.amber { border-left-color: var(--amber); }
    .item.rose { border-left-color: var(--rose); }
    .meta { color: var(--muted); font-size: 13px; margin-top: 4px; overflow-wrap: anywhere; }
    .empty {
      color: var(--muted);
      background: var(--soft);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .steps { margin: 0; padding-left: 20px; }
    .steps li { margin: 6px 0; }
    .mode-switch {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .mode-switch button {
      min-height: 44px;
      padding: 7px 12px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      font-size: 14px;
      cursor: pointer;
      transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease;
    }
    .mode-switch button:hover,
    .mode-switch button[aria-pressed="true"] {
      border-color: #b9ccff;
      background: #eef4ff;
      color: #1d4ed8;
    }
    .cta-card {
      border-left: 4px solid var(--blue);
      background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
    }
    .cta-layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(260px, 340px);
      gap: 16px;
      align-items: start;
    }
    .cta-title { margin: 4px 0 8px; font-size: 22px; }
    .eyebrow {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .command-stack {
      display: grid;
      gap: 8px;
    }
    .inline-button.primary {
      border-color: #1d4ed8;
      background: #2563eb;
      color: #fff;
    }
    .inline-button.primary:hover {
      border-color: #1d4ed8;
      background: #1d4ed8;
      color: #fff;
    }
    .copy-feedback {
      min-height: 20px;
      color: var(--green);
      font-size: 13px;
    }
    [hidden] { display: none !important; }
    table {
      display: block;
      width: 100%;
      max-width: 100%;
      overflow-x: auto;
      border-collapse: collapse;
      font-size: 14px;
      -webkit-overflow-scrolling: touch;
    }
    thead, tbody, tr { width: 100%; }
    th, td { text-align: left; border-bottom: 1px solid var(--line); padding: 9px 8px; vertical-align: top; }
    th { color: var(--muted); font-weight: 650; background: #fbfdff; }
    code {
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      background: #eef3f8;
      border: 1px solid #d8e2ec;
      border-radius: 5px;
      padding: 1px 4px;
      font-size: 0.92em;
    }
    pre {
      overflow: auto;
      white-space: pre-wrap;
      background: #13202c;
      color: #eef6ff;
      border-radius: 8px;
      padding: 14px;
    }
    pre code {
      background: transparent;
      border: 0;
      color: inherit;
      padding: 0;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }
    .toolbar a, .toolbar button {
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      font-size: 14px;
      cursor: pointer;
      min-height: 44px;
    }
    .toolbar button.active {
      border-color: var(--blue);
      color: var(--blue);
      background: #eef4ff;
    }
    .inline-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 7px 11px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      font-size: 14px;
      cursor: pointer;
      white-space: nowrap;
      transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease;
    }
    .review-mark { min-width: 112px; }
    .inline-button:hover {
      border-color: #b9ccff;
      background: #eef4ff;
      color: #1d4ed8;
    }
    .inline-button[disabled] {
      cursor: not-allowed;
      opacity: 0.58;
    }
    .review-actions {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin: 0 0 14px;
    }
    .review-status {
      min-height: 24px;
      color: var(--muted);
      font-size: 14px;
    }
    .source-path {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 16px;
      word-break: break-all;
    }
    .md-view {
      max-width: 980px;
      margin: 0 auto;
    }
    .md-view h1 { margin-top: 0; font-size: 28px; }
    .md-view h2 {
      margin-top: 28px;
      padding-top: 10px;
      border-top: 1px solid var(--line);
    }
    .md-view h3 { margin-top: 22px; }
    .md-view ul, .md-view ol { padding-left: 22px; }
    .md-view li { margin: 5px 0; }
    .md-view blockquote {
      margin: 14px 0;
      padding: 10px 14px;
      border-left: 4px solid var(--blue);
      background: #f0f5ff;
      color: #24384e;
    }
    .md-view table {
      display: block;
      overflow-x: auto;
      white-space: normal;
      margin: 12px 0 18px;
    }
    .wikilink {
      display: inline-flex;
      align-items: center;
      border: 1px solid #cdddeb;
      background: #f4f8fb;
      color: #1e5678;
      border-radius: 999px;
      padding: 0 7px;
      font-size: 0.92em;
    }
    footer { color: var(--muted); font-size: 12px; padding: 12px 0 24px; }
    @media (max-width: 840px) {
      .panel, .metric { grid-column: 1 / -1; }
      .cta-layout { grid-template-columns: 1fr; }
      h1 { font-size: 28px; }
      .wrap { padding-left: 16px; padding-right: 16px; }
      .nav { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 4px; }
      .nav a { flex: 0 0 auto; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
      }
    }
    """


def page_script(body: str) -> str:
    blocks: list[str] = []
    if "data-copy=" in body:
        blocks.append(
            """
      const feedback = new Map();
      document.querySelectorAll("[data-copy]").forEach((button) => {
        button.addEventListener("click", async () => {
          const text = button.getAttribute("data-copy") || "";
          try {
            await navigator.clipboard.writeText(text);
            button.textContent = "已复制";
            clearTimeout(feedback.get(button));
            feedback.set(button, setTimeout(() => { button.textContent = button.getAttribute("data-label") || "复制命令"; }, 1600));
          } catch (_error) {
            const target = button.nextElementSibling;
            if (target && target.classList.contains("copy-feedback")) {
              target.textContent = text;
            }
          }
        });
      });"""
        )
    if "data-mode-button" in body or "data-mode=" in body:
        blocks.append(
            """
      const modeButtons = [...document.querySelectorAll("[data-mode-button]")];
      const modeSections = [...document.querySelectorAll("[data-mode]")];
      const setMode = (mode) => {
        modeButtons.forEach((button) => {
          button.setAttribute("aria-pressed", String(button.getAttribute("data-mode-button") === mode));
        });
        modeSections.forEach((section) => {
          const modes = (section.getAttribute("data-mode") || "").split(/\\s+/);
          section.hidden = mode !== "all" && !modes.includes(mode);
        });
        localStorage.setItem("rw-dashboard-mode", mode);
      };
      modeButtons.forEach((button) => button.addEventListener("click", () => setMode(button.getAttribute("data-mode-button") || "all")));
      setMode(localStorage.getItem("rw-dashboard-mode") || "all");"""
        )
    if not blocks:
        return ""
    return """
  <script>
    (() => {
%s
    })();
  </script>""" % "\n".join(blocks)


def shell(title: str, subtitle: str, current: str, body: str, output: Path) -> str:
    evidence_page = active_project_path("literature", "evidence_locator_table.html")
    verification_page = active_project_path("evidence", "page_verification_queue.html")
    incoming_page = active_project_path("literature", "incoming_pdf_triage.html")
    writing_page = active_project_path("manuscript", "writing_panel.html")
    nav = [
        ("总览", ROOT / "study_dashboard.html"),
        ("今日精读", PAPER_READING / "today.html"),
        ("论文归档", PAPER_READING / "index.html"),
        ("知识卡", KNOWLEDGE_CARDS / "index.html"),
        ("复习", REVIEW_TODAY),
        ("知识图谱", KNOWLEDGE_GRAPH / "index.html"),
        ("搜索", SEARCH_INDEX_HTML),
        ("学习日志", HTML_LOGS / "index.html"),
        ("总状态", WORKFLOW_STATE_HTML),
        ("行动队列", ACTION_QUEUE_HTML),
        ("项目协作", COLLABORATION_HTML),
        ("归档策略", ARCHIVE_POLICY_HTML),
        ("工作流体检", WORKFLOW_HEALTH),
        ("Vault 首页", PAPER_VIEWS / "vault-home.html"),
    ]
    for label, path in [("PDF分拣", incoming_page), ("证据定位", evidence_page), ("页码核验", verification_page), ("论文写作", writing_page)]:
        if path.exists():
            nav.insert(-1, (label, path))
    nav_items: list[str] = []
    for label, path in nav:
        current_attr = ' aria-current="page"' if label == current else ""
        nav_items.append(f'<a href="{href(path, output)}"{current_attr}>{esc(label)}</a>')
    nav_html = "\n".join(nav_items)
    script = page_script(body)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>{common_css()}</style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <header>
    <div class="wrap">
      <h1>{esc(title)}</h1>
      <p class="sub">{esc(subtitle)}</p>
      <nav class="nav">{nav_html}</nav>
    </div>
  </header>
  <main class="wrap" id="main-content">
{body}
  </main>
  <footer class="wrap">Generated by scripts/build_learning_dashboard.py.</footer>
{script}
</body>
</html>
"""


def copy_button(command: str, label: str = "复制命令") -> str:
    return (
        f'<button type="button" class="inline-button" data-copy="{esc(command)}" data-label="{esc(label)}">{esc(label)}</button>'
        '<div class="copy-feedback" aria-live="polite"></div>'
    )


def dashboard_command_for_action(action: dict[str, object]) -> str:
    kind = str(action.get("kind", ""))
    entrypoint = str(action.get("entrypoint", "study_dashboard.html"))
    if kind.startswith("review"):
        return "make review-server-ensure"
    if kind.startswith("audit"):
        return "make workflow-audit"
    if kind == "project":
        return f"open {entrypoint}"
    return "make learning-dashboard"


def dashboard_top_action(out: Path) -> str:
    queue = read_json(ACTION_QUEUE_JSON, {})
    actions = queue.get("actions", []) if isinstance(queue, dict) else []
    action = actions[0] if actions else {}
    title = str(action.get("title", "从今日精读入口继续推进"))
    reason = str(action.get("reason", "当前没有阻塞项；优先继续阅读、复习或核验证据。"))
    entrypoint = str(action.get("entrypoint", href(PAPER_READING / "today.html", out)))
    target = ROOT / entrypoint if entrypoint and "://" not in entrypoint else PAPER_READING / "today.html"
    command = dashboard_command_for_action(action) if action else f"open {href(PAPER_READING / 'today.html', out)}"
    link = href(target, out) if target.exists() else esc(entrypoint or "paper_reading/today.html")
    return f"""
      <section class="panel wide cta-card" data-mode="all reading writing evidence maintenance">
        <div class="cta-layout">
          <div>
            <p class="eyebrow">Today's primary action</p>
            <h2 class="cta-title"><a href="{link}">{esc(title)}</a></h2>
            <p>{esc(reason)}</p>
          </div>
          <div class="command-stack">
            <a class="inline-button primary" href="{link}">打开入口</a>
            {copy_button(command)}
            <code>{esc(command)}</code>
          </div>
        </div>
      </section>
"""


def mode_switch() -> str:
    buttons = [
        ("all", "全部"),
        ("reading", "阅读"),
        ("writing", "写作"),
        ("evidence", "证据"),
        ("maintenance", "维护"),
    ]
    return (
        """
      <section class="panel wide" data-mode="all reading writing evidence maintenance">
        <h2>工作模式</h2>
        <div class="mode-switch" role="group" aria-label="工作模式筛选">
"""
        + "\n".join(
            f'          <button type="button" data-mode-button="{value}" aria-pressed="{str(value == "all").lower()}">{label}</button>'
            for value, label in buttons
        )
        + """
        </div>
      </section>
"""
    )


def item_list(paths: list[Path], output: Path, color: str = "") -> str:
    if not paths:
        return '<div class="empty">暂无可展示条目。下一次自动任务运行后会补充这里。</div>'
    blocks = []
    for path in paths[:12]:
        title = html_title(path) if path.suffix == ".html" else md_title(path)
        cls = f"item {color}".strip()
        blocks.append(
            f'<div class="{cls}"><a href="{display_href(path, output)}">{esc(title)}</a>'
            f'<div class="meta">{esc(path.relative_to(ROOT))}</div></div>'
        )
    return '<div class="list">' + "\n".join(blocks) + "</div>"


def build_dashboard() -> None:
    out = ROOT / "study_dashboard.html"
    evidence_page = active_project_path("literature", "evidence_locator_table.html")
    verification_page = active_project_path("evidence", "page_verification_queue.html")
    incoming_page = active_project_path("literature", "incoming_pdf_triage.html")
    writing_page = active_project_path("manuscript", "writing_panel.html")
    pages = paper_pages()
    log_pages = list_html(HTML_LOGS)
    concepts = list_md(CONCEPTS)
    methods = list_md(METHODS)
    due = due_reviews()
    node_count, edge_count, top_nodes = graph_counts()
    today_entry = PAPER_READING / "today.html"
    latest = pages[0] if pages else None
    latest_audit = latest_file(VAULT / "07_Codex_Logs" / "workflow_audits", "*-workflow-audit.md")
    latest_sweep = latest_file(VAULT / "07_Codex_Logs" / "file_sweeps", "*-file-sweep.md")
    latest_backup = latest_file(ROOT / "backups", "*.zip")
    primary_action_panel = dashboard_top_action(out).strip()
    mode_panel = mode_switch().strip()
    today_panel = (
        f"""
      <section class="panel wide" data-mode="reading">
        <h2>固定入口</h2>
        <p>以后每天只点同一个入口即可：<a href="{href(today_entry, out)}">今日精读入口</a>。</p>
        <p>当前会打开：<strong>{esc(html_title(latest))}</strong></p>
      </section>
"""
        if latest
        else f"""
      <section class="panel wide" data-mode="reading">
        <h2>固定入口</h2>
        <div class="empty">固定入口已预留在 <a href="{href(today_entry, out)}">paper_reading/today.html</a>，但当前还没有可打开的精读页。</div>
      </section>
"""
    )
    body = f"""
    <section class="grid">
      {primary_action_panel}
      {mode_panel}

      <div class="metric"><b>{len(pages)}</b><span>论文精读 HTML</span></div>
      <div class="metric"><b>{len(concepts) + len(methods)}</b><span>概念/方法知识卡</span></div>
      <div class="metric"><b>{node_count}/{edge_count}</b><span>图谱节点/关系边</span></div>
      <div class="metric"><b>{len(due)}</b><span>今日应复习</span></div>

      {today_panel}

      <section class="panel wide" data-mode="maintenance evidence writing">
        <h2>系统健康与备份</h2>
        <div class="list">
          <div class="item"><a href="{href(SEARCH_INDEX_HTML, out)}">全局搜索入口</a><div class="meta">搜索论文、知识卡、项目文件、日志和图谱相关资产。</div></div>
          <div class="item green"><a href="{href(WORKFLOW_STATE_HTML, out)}">工作流总状态</a><div class="meta">聚合项目、复习、搜索、图谱和审计状态。</div></div>
          <div class="item amber"><a href="{href(ACTION_QUEUE_HTML, out)}">行动队列</a><div class="meta">按优先级排列今天最该处理的事项。</div></div>
          <div class="item green"><a href="{href(COLLABORATION_HTML, out)}">项目协作层</a><div class="meta">查看用户待确认、Codex 可推进和项目入口。</div></div>
          <div class="item amber"><a href="{href(ARCHIVE_POLICY_HTML, out)}">自动归档策略</a><div class="meta">查看备份、日志、生成页和缓存文件的归档策略。</div></div>
          <div class="item"><a href="{href(WORKFLOW_HEALTH, out)}">工作流体检页</a><div class="meta">检查入口、链接、镜像页、图谱、归档、复习队列和备份。</div></div>
          {f'<div class="item green"><a href="{href(incoming_page, out)}">Incoming PDF 分拣</a><div class="meta">扫描 incoming 全文，匹配矩阵并建议入库、建 Reader 或归档重复件。</div></div>' if incoming_page.exists() else ''}
          {f'<div class="item green"><a href="{href(evidence_page, out)}">证据核验表</a><div class="meta">集中查看主张、文献、Reader block、页码和核验状态。</div></div>' if evidence_page.exists() else ''}
          {f'<div class="item amber"><a href="{href(verification_page, out)}">页码级证据核验队列</a><div class="meta">按优先级列出 claim 到 source block、页码和 read_status 的核验任务。</div></div>' if verification_page.exists() else ''}
          {f'<div class="item amber"><a href="{href(writing_page, out)}">论文写作推进面板</a><div class="meta">把已读文献转成研究问题、变量指标、机制链和可写段落。</div></div>' if writing_page.exists() else ''}
          <div class="item rose"><a href="{href(REVIEW_TODAY, out)}">今日复习入口</a><div class="meta">{len(due)} 个知识点今天需要主动回忆。</div></div>
          <div class="item green">{f'<a href="{href(BACKUP_INDEX, out)}">备份索引</a>' if BACKUP_INDEX.exists() else '备份索引'}<div class="meta">{esc(latest_backup.name if latest_backup else '尚未生成备份；运行 make workflow-backup。')}</div></div>
          <div class="item amber"><a href="{href(WORKFLOW_HEALTH, out)}">最近审计概览</a><div class="meta">{esc(str(latest_audit.relative_to(ROOT)) if latest_audit else '运行 make workflow-audit 后生成。')}</div></div>
          <div class="item rose">最近文件归类清单<div class="meta">{esc(str(latest_sweep.relative_to(ROOT)) if latest_sweep else '运行 make codex-sweep 后生成。')}</div></div>
        </div>
      </section>

      <section class="panel wide" data-mode="reading">
        <h2>今日使用顺序</h2>
        <ol class="steps">
          <li>早上从固定入口 <code>paper_reading/today.html</code> 进入，直接打开当天主读页。</li>
          <li>顺着页面进入新建/更新的概念卡、方法卡和来源论文笔记。</li>
          <li>打开今日复习入口，先主动回忆到期知识卡。</li>
          <li>打开知识图谱入口，查看这篇论文带来的新关系。</li>
          <li>晚上查看学习日志入口，确认归档、复习问题和明日行动。</li>
        </ol>
      </section>

      <section class="panel" data-mode="reading">
        <h2>最近论文精读</h2>
        {item_list(pages, out, "green")}
      </section>
      <section class="panel" data-mode="reading">
        <h2>最近学习日志</h2>
        {item_list(log_pages, out, "amber")}
      </section>
      <section class="panel" data-mode="reading writing">
        <h2>最近知识卡</h2>
        {item_list((concepts + methods)[:12], out, "rose")}
      </section>
      <section class="panel" data-mode="reading evidence">
        <h2>图谱高连接节点</h2>
        {top_nodes_table(top_nodes)}
      </section>
    </section>
"""
    write_text_if_changed(out, shell("ResearchWorkflow 学习仪表盘", "论文精读、知识卡、知识图谱和学习日志的统一入口。", "总览", body, out))


def top_nodes_table(top_nodes: list[tuple[str, int]]) -> str:
    if not top_nodes:
        return '<div class="empty">暂无图谱关系。运行 make obsidian-graph 后会显示高连接节点。</div>'
    rows = "\n".join(f"<tr><td>{esc(name)}</td><td>{count}</td></tr>" for name, count in top_nodes)
    return f"<table><thead><tr><th>节点</th><th>连接数</th></tr></thead><tbody>{rows}</tbody></table>"


def render_inline_markdown(text: str, source: Path | None = None, output: Path | None = None) -> str:
    value = esc(text)
    value = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", value)
    value = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", lambda m: f'<span class="wikilink">{m.group(2)}</span>', value)
    value = re.sub(r"\[\[([^\]]+)\]\]", lambda m: f'<span class="wikilink">{m.group(1)}</span>', value)
    value = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{display_link_target(m.group(2), source, output)}">{m.group(1)}</a>',
        value,
    )
    return value


def strip_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if not match:
        return "", text
    return match.group(1).strip(), text[match.end() :]


def frontmatter_table(frontmatter: str, source: Path | None = None, output: Path | None = None) -> str:
    if not frontmatter:
        return ""
    rows: list[str] = []
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        rows.append(f"<tr><th>{esc(key.strip())}</th><td>{render_inline_markdown(value.strip(), source, output)}</td></tr>")
    if not rows:
        return ""
    return f'<section class="frontmatter"><h2>元数据</h2><table><tbody>{"".join(rows)}</tbody></table></section>'


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    if len(cells) < 2:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def table_to_html(lines: list[str], source: Path | None = None, output: Path | None = None) -> str:
    if len(lines) < 2:
        return ""
    headers = split_table_row(lines[0])
    body_rows = [split_table_row(line) for line in lines[2:]]
    head = "".join(f"<th>{render_inline_markdown(cell, source, output)}</th>" for cell in headers)
    body = []
    for row in body_rows:
        padded = row + [""] * max(0, len(headers) - len(row))
        body.append("<tr>" + "".join(f"<td>{render_inline_markdown(cell, source, output)}</td>" for cell in padded[: len(headers)]) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_markdown(text: str, source: Path | None = None, output: Path | None = None) -> str:
    frontmatter, body = strip_frontmatter(text)
    lines = body.splitlines()
    parts: list[str] = [frontmatter_table(frontmatter, source, output)] if frontmatter else []
    paragraph: list[str] = []
    list_kind: str | None = None
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{render_inline_markdown(' '.join(paragraph), source, output)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_kind
        if list_kind:
            parts.append(f"</{list_kind}>")
            list_kind = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            fence_language = stripped.strip("`").strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            language_class = f' class="language-{esc(fence_language)}"' if fence_language else ""
            parts.append(f"<pre><code{language_class}>{esc(chr(10).join(code_lines))}</code></pre>")
            continue

        if "|" in line and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            flush_paragraph()
            flush_list()
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            parts.append(table_to_html(table_lines, source, output))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)), 6)
            parts.append(f"<h{level}>{render_inline_markdown(heading.group(2), source, output)}</h{level}>")
            i += 1
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            flush_paragraph()
            flush_list()
            parts.append(f"<blockquote>{render_inline_markdown(quote.group(1), source, output)}</blockquote>")
            i += 1
            continue

        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        if unordered:
            flush_paragraph()
            if list_kind != "ul":
                flush_list()
                parts.append("<ul>")
                list_kind = "ul"
            parts.append(f"<li>{render_inline_markdown(unordered.group(1), source, output)}</li>")
            i += 1
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            if list_kind != "ol":
                flush_list()
                parts.append("<ol>")
                list_kind = "ol"
            parts.append(f"<li>{render_inline_markdown(ordered.group(1), source, output)}</li>")
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    flush_list()
    return "\n".join(part for part in parts if part)


def rewrite_paper_markdown_links() -> None:
    href_pattern = re.compile(r'href=(["\'])([^"\']+?\.md(?:#[^"\']*)?)\1')
    for page in paper_pages():
        text = page.read_text(encoding="utf-8", errors="ignore")

        def replace(match: re.Match[str]) -> str:
            quote_char = match.group(1)
            source = local_markdown_source(page, match.group(2))
            if not source:
                return match.group(0)
            view = html_view_for_local_path(source)
            return f"href={quote_char}{href(view, page)}{quote_char}"

        rewritten = href_pattern.sub(replace, text)
        if rewritten != text:
            write_text_if_changed(page, rewritten)


def write_paper_markdown_view(source: Path) -> Path:
    out = paper_markdown_view_path(source)
    title = paper_markdown_view_title(source)
    subtitle = paper_markdown_view_subtitle(source)
    if source.exists():
        article = render_markdown(source.read_text(encoding="utf-8", errors="ignore"), source, out)
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(KNOWLEDGE_GRAPH / 'index.html', out)}">查看知识图谱</a>
        </div>
        <div class="source-path">源文件：{esc(relative_label(source))}</div>
        <article class="md-view">
{article}
        </article>
      </section>
    </section>
"""
    else:
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar"><a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a></div>
        <div class="empty">源文件不存在：{esc(relative_label(source))}</div>
      </section>
    </section>
"""
    write_text_if_changed(out, shell(title, subtitle, "今日精读", body, out))
    return out


def build_markdown_views() -> None:
    PAPER_VIEWS.mkdir(parents=True, exist_ok=True)
    sources = markdown_sources_from_paper_pages(paper_pages())
    expected_outputs = {paper_markdown_view_path(source).resolve() for source in sources}
    for stale in PAPER_VIEWS.glob("*.html"):
        if stale.resolve() not in expected_outputs:
            stale.unlink()
    for source in sources:
        write_paper_markdown_view(source)


def build_knowledge_card_views() -> None:
    KNOWLEDGE_CARD_VIEWS.mkdir(parents=True, exist_ok=True)
    for source in [*list_md(CONCEPTS), *list_md(METHODS)]:
        out = card_view_path(source)
        card_type = "概念卡" if source.parent == CONCEPTS else "方法卡"
        article = render_markdown(source.read_text(encoding="utf-8", errors="ignore"), source, out)
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(KNOWLEDGE_CARDS / 'index.html', out)}">返回知识卡入口</a>
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(KNOWLEDGE_GRAPH / 'index.html', out)}">查看知识图谱</a>
        </div>
        <div class="source-path">源文件：{esc(source.relative_to(ROOT))}</div>
        <article class="md-view">
{article}
        </article>
      </section>
    </section>
"""
        write_text_if_changed(out, shell(f"{card_type}：{md_title(source)}", "可直接在浏览器阅读的知识卡镜像页。", "知识卡", body, out))


def build_log_views() -> None:
    LOG_VIEWS.mkdir(parents=True, exist_ok=True)
    for source in list_md(LEARNING_SESSIONS):
        out = log_view_path(source)
        article = render_markdown(source.read_text(encoding="utf-8", errors="ignore"), source, out)
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(HTML_LOGS / 'index.html', out)}">返回学习日志入口</a>
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(KNOWLEDGE_GRAPH / 'index.html', out)}">查看知识图谱</a>
        </div>
        <div class="source-path">源文件：{esc(source.relative_to(ROOT))}</div>
        <article class="md-view">
{article}
        </article>
      </section>
    </section>
"""
        write_text_if_changed(out, shell(f"学习日志：{md_title(source)}", "可直接在浏览器阅读的学习会话镜像页。", "学习日志", body, out))


def directory_item_link(path: Path, output: Path) -> str:
    target = html_view_for_local_path(path)
    title = md_title(path) if path.suffix == ".md" else html_title(path) if path.suffix == ".html" else path.name
    return (
        f'<div class="item"><a href="{href(target, output)}">{esc(title)}</a>'
        f'<div class="meta">{esc(relative_label(path))}</div></div>'
    )


def collect_directory_sources(seeds: list[Path]) -> list[Path]:
    directories: dict[Path, Path] = {}
    queue = [source for source in seeds if source.exists() and source.is_dir()]
    while queue:
        current = queue.pop(0)
        resolved = current.resolve()
        if resolved in directories:
            continue
        directories[resolved] = current
        for child in sorted(current.iterdir(), key=lambda path: path.name.lower()):
            if child.name.startswith(".") or not child.is_dir():
                continue
            queue.append(child)
    return sorted(directories.values(), key=relative_label)


def build_directory_views() -> None:
    DIR_VIEWS.mkdir(parents=True, exist_ok=True)
    seeds = directory_sources_from_markdown(markdown_sources_from_paper_pages(paper_pages()))
    sources = collect_directory_sources(seeds)
    expected_outputs = {directory_view_path(source).resolve() for source in sources}
    for stale in DIR_VIEWS.glob("*.html"):
        if stale.resolve() not in expected_outputs:
            stale.unlink()
    for source in sources:
        out = directory_view_path(source)
        children: list[str] = []
        if source.exists():
            for child in sorted(source.iterdir(), key=lambda path: (path.is_file(), path.name.lower())):
                if child.name.startswith("."):
                    continue
                if child.is_dir() or child.suffix in {".md", ".html"}:
                    if child.suffix == ".md":
                        write_paper_markdown_view(child)
                    children.append(directory_item_link(child, out))
        items = "\n".join(children) if children else '<div class="empty">这个文件夹暂时没有可浏览的 Markdown/HTML 条目。</div>'
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(KNOWLEDGE_GRAPH / 'index.html', out)}">查看知识图谱</a>
        </div>
        <div class="source-path">源文件夹：{esc(relative_label(source))}</div>
        <div class="list">
{items}
        </div>
      </section>
    </section>
"""
        write_text_if_changed(out, shell(f"文件夹入口：{source.name}", "本地文件夹的浏览器友好索引页。", "今日精读", body, out))


def graph_kind(raw_type: str) -> str:
    lower = raw_type.lower()
    if "concept" in lower or "02_" in lower:
        return "concept"
    if "method" in lower or "03_" in lower:
        return "method"
    if "project" in lower:
        return "project"
    if "literature" in lower or "cnki" in lower or "15_" in lower:
        return "literature"
    if "learning" in lower or "log" in lower or "session" in lower:
        return "learning"
    return "linked"


def graph_data() -> dict[str, list[dict[str, object]]]:
    node_rows = csv_rows(GRAPH_DIR / "obsidian_nodes.csv")
    edge_rows = csv_rows(GRAPH_DIR / "obsidian_edges.csv")
    seen_edges: set[tuple[str, str]] = set()
    degree: Counter[str] = Counter()
    edges: list[dict[str, object]] = []
    node_map: dict[str, dict[str, object]] = {}

    for row in node_rows:
        node_id = row.get("Id", "").strip()
        if not node_id:
            continue
        raw_type = row.get("Type", "").strip()
        node_map[node_id] = {
            "id": node_id,
            "label": row.get("Label", "").strip() or node_id,
            "type": raw_type or "linked",
            "kind": graph_kind(raw_type),
        }

    for row in edge_rows:
        source = row.get("Source", "").strip()
        target = row.get("Target", "").strip()
        if not source or not target or source == target:
            continue
        key = (source, target)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        degree[source] += 1
        degree[target] += 1
        edges.append(
            {
                "source": source,
                "target": target,
                "label": row.get("Label", "").strip() or row.get("Type", "").strip() or "link",
            }
        )
        for node_id in (source, target):
            if node_id not in node_map:
                node_map[node_id] = {"id": node_id, "label": node_id, "type": "linked", "kind": "linked"}

    nodes = []
    for node_id, node in node_map.items():
        item = dict(node)
        item["degree"] = degree[node_id]
        nodes.append(item)
    nodes.sort(key=lambda item: (-int(item.get("degree", 0)), str(item.get("label", ""))))
    return {"nodes": nodes, "edges": edges}


def build_paper_today() -> None:
    PAPER_READING.mkdir(parents=True, exist_ok=True)
    out = PAPER_READING / "today.html"
    archive = PAPER_READING / "index.html"
    pages = paper_pages()
    latest = pages[0] if pages else None
    if latest:
        target = href(latest, out)
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <h2>今日固定入口</h2>
        <p>这个页面是稳定入口。以后每天直接打开它，系统会自动跳到当天最新的主读论文。</p>
      </section>
      <section class="panel">
        <h2>正在打开</h2>
        <p><strong>{esc(html_title(latest))}</strong></p>
        <p>如果没有自动跳转，请点击 <a href="{target}">打开今天的精读页</a>。</p>
      </section>
      <section class="panel">
        <h2>备用入口</h2>
        <ol class="steps">
          <li>固定入口路径：<code>paper_reading/today.html</code></li>
          <li>历史归档：<a href="{href(archive, out)}">paper_reading/index.html</a></li>
          <li>总仪表盘：<a href="{href(ROOT / 'study_dashboard.html', out)}">study_dashboard.html</a></li>
        </ol>
      </section>
    </section>
    <script>
      window.setTimeout(function () {{
        window.location.replace("{target}");
      }}, 120);
    </script>
"""
        title = "今日精读入口"
        subtitle = "固定不变的每日论文入口。打开后自动进入当天主读页。"
    else:
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <h2>今日固定入口</h2>
        <div class="empty">当前还没有可打开的论文精读页。等下一次自动任务生成当日主读页后，这里会自动更新。</div>
      </section>
      <section class="panel">
        <h2>你仍然可以打开</h2>
        <ol class="steps">
          <li><a href="{href(archive, out)}">论文精读归档</a></li>
          <li><a href="{href(ROOT / 'study_dashboard.html', out)}">学习仪表盘</a></li>
        </ol>
      </section>
    </section>
"""
        title = "今日精读入口"
        subtitle = "固定不变的每日论文入口。当前还没有生成今日主读页。"
    write_text_if_changed(out, shell(title, subtitle, "今日精读", body, out))


def build_paper_index() -> None:
    PAPER_READING.mkdir(parents=True, exist_ok=True)
    out = PAPER_READING / "index.html"
    today = PAPER_READING / "today.html"
    pages = paper_pages()
    latest = pages[0] if pages else None
    fixed_entry = (
        f"""
      <section class="panel wide">
        <h2>固定入口</h2>
        <p>以后每天直接点 <a href="{href(today, out)}">今日精读入口</a>，不需要再找当天文件。</p>
        <p>当前主读：<strong>{esc(html_title(latest))}</strong></p>
      </section>
"""
        if latest
        else f"""
      <section class="panel wide">
        <h2>固定入口</h2>
        <div class="empty">固定入口已预留在 <a href="{href(today, out)}">paper_reading/today.html</a>，但当前还没有生成主读页。</div>
      </section>
"""
    )
    body = f"""
    <section class="grid">
      {fixed_entry}
      <section class="panel wide">
        <h2>论文精读时间线</h2>
        {item_list(pages, out, "green")}
      </section>
      <section class="panel">
        <h2>每篇论文应连接到</h2>
        <ol class="steps">
          <li>Obsidian 论文笔记：<code>vault/01_Literature/</code></li>
          <li>概念卡和方法卡：<code>vault/02_Concepts/</code>、<code>vault/03_Methods/</code></li>
          <li>知识图谱：<code>knowledge_graph/index.html</code></li>
          <li>复习队列：<code>vault/14_Review_Queue/review_queue.csv</code></li>
        </ol>
      </section>
      <section class="panel">
        <h2>推荐阅读顺序</h2>
        <ol class="steps">
          <li>先点固定入口，直接进入当天推荐页。</li>
          <li>再看研究问题、方法、证据和图表逻辑。</li>
          <li>最后进入知识卡和图谱看关联。</li>
        </ol>
      </section>
    </section>
"""
    write_text_if_changed(out, shell("论文精读归档", "固定入口请用 today.html；这里保留历史时间线。", "论文归档", body, out))


def build_logs_index() -> None:
    HTML_LOGS.mkdir(parents=True, exist_ok=True)
    out = HTML_LOGS / "index.html"
    sessions = list_md(LEARNING_SESSIONS)
    body = f"""
    <section class="grid">
      <section class="panel">
        <h2>HTML 学习日志</h2>
        {item_list(list_html(HTML_LOGS), out, "amber")}
      </section>
      <section class="panel">
        <h2>Markdown 学习会话</h2>
        {item_list(sessions, out)}
      </section>
      <section class="panel wide">
        <h2>晚间归档检查</h2>
        <ol class="steps">
          <li>今天的论文页面是否已经链接到知识卡和图谱。</li>
          <li>新增知识卡是否已经进入复习队列。</li>
          <li>图谱和仪表盘是否已经刷新。</li>
          <li>不确定文件是否已记录为待处理，而不是被删除。</li>
        </ol>
      </section>
    </section>
"""
    write_text_if_changed(out, shell("学习日志入口", "每日学习记录、归档摘要和明日行动。", "学习日志", body, out))


def build_cards_index() -> None:
    KNOWLEDGE_CARDS.mkdir(parents=True, exist_ok=True)
    out = KNOWLEDGE_CARDS / "index.html"
    concepts = list_md(CONCEPTS)
    methods = list_md(METHODS)
    due = due_reviews()
    due_rows = "\n".join(
        f"<tr><td>{esc(row.get('title', ''))}</td><td>{esc(row.get('type', ''))}</td><td>{esc(row.get('next_review', ''))}</td><td>{esc(row.get('prompt', ''))}</td></tr>"
        for row in due[:12]
    )
    due_table = (
        f"<table><thead><tr><th>标题</th><th>类型</th><th>复习日</th><th>提示</th></tr></thead><tbody>{due_rows}</tbody></table>"
        if due_rows
        else '<div class="empty">今天没有到期复习项。</div>'
    )
    body = f"""
    <section class="grid">
      <section class="panel">
        <h2>概念卡</h2>
        {item_list(concepts, out, "rose")}
      </section>
      <section class="panel">
        <h2>方法卡</h2>
        {item_list(methods, out, "green")}
      </section>
      <section class="panel wide">
        <h2>今日复习队列</h2>
        <p><a href="{href(REVIEW_TODAY, out)}">打开独立复习页</a></p>
        {due_table}
      </section>
    </section>
"""
    write_text_if_changed(out, shell("知识卡入口", "概念、方法、复习问题和与论文的连接。", "知识卡", body, out))


def review_items_table(items: list[dict[str, object]], output: Path, limit: int = 20) -> str:
    if not items:
        return '<div class="empty">暂无条目。</div>'
    rows: list[str] = []
    for item in items[:limit]:
        display_path = str(item.get("display_path", ""))
        title = esc(item.get("title", ""))
        title_html = f'<a href="{href(ROOT / display_path, output)}">{title}</a>' if display_path else title
        delta = item.get("days_delta")
        if isinstance(delta, int):
            delta_text = "今天" if delta == 0 else f"{abs(delta)} 天前" if delta < 0 else f"{delta} 天后"
        else:
            delta_text = ""
        status = str(item.get("status", ""))
        if status == "learned_today":
            delta_text = "今日已学习"
        command = f"make review-studied ID={item.get('id', '')}"
        if status == "learned_today":
            action = '<span class="meta">已学习</span>'
        else:
            action = (
                f'<button class="inline-button review-mark" type="button" '
                f'data-review-id="{esc(item.get("id", ""))}">标记已学习</button>'
            )
        rows.append(
            "<tr>"
            f"<td>{title_html}</td>"
            f"<td>{esc(item.get('type', ''))}</td>"
            f"<td>{esc(item.get('stage', ''))}</td>"
            f"<td>{esc(item.get('next_review', ''))}</td>"
            f"<td>{esc(delta_text)}</td>"
            f"<td>{esc(item.get('prompt', ''))}</td>"
            f"<td>{action}</td>"
            f"<td><code>{esc(command)}</code></td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>知识卡</th><th>类型</th><th>阶段</th><th>下次复习</th><th>状态</th><th>主动回忆问题</th><th>操作</th><th>备用命令</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def review_mark_script() -> str:
    return """<script>
    (() => {
      const endpoint = "http://127.0.0.1:8765/review/studied";
      const healthEndpoint = "http://127.0.0.1:8765/health";
      const status = document.querySelector("[data-review-status]");
      const serviceHelp = "工作流启动时会自动检查；若当前未连接，请运行 make review-server-ensure。备用命令仍然可用。";
      const setStatus = (message) => {
        if (status) status.textContent = message;
      };
      const checkService = async () => {
        const response = await fetch(healthEndpoint, {method: "GET"});
        if (!response.ok) throw new Error("本地写回服务未启动");
      };
      const mark = async (payload, button) => {
        const buttons = button ? [button] : Array.from(document.querySelectorAll(".review-mark, [data-review-bulk]"));
        buttons.forEach((item) => { item.disabled = true; });
        setStatus("正在写回复习状态...");
        try {
          await checkService();
          const response = await fetch(endpoint, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
          });
          const data = await response.json();
          if (!response.ok || !data.ok) {
            throw new Error(data.error || "写回失败");
          }
          setStatus(`已标记 ${data.marked_count} 个知识卡，页面即将刷新。`);
          window.setTimeout(() => window.location.reload(), 900);
        } catch (error) {
          setStatus(`无法写回：${error.message}。${serviceHelp}`);
          buttons.forEach((item) => { item.disabled = false; });
        }
      };
      checkService()
        .then(() => setStatus("本地写回服务已连接，可以直接标记已学习。"))
        .catch(() => setStatus(`本地写回服务未启动。${serviceHelp}`));
      document.querySelectorAll(".review-mark").forEach((button) => {
        button.addEventListener("click", () => {
          mark({id: button.dataset.reviewId}, button);
        });
      });
      const bulk = document.querySelector("[data-review-bulk]");
      if (bulk) {
        bulk.addEventListener("click", () => mark({all_due: true}, null));
      }
    })();
    </script>"""


def build_review_today() -> None:
    write_review_state()
    out = REVIEW_TODAY
    state = build_review_state_payload()
    summary = state["summary"]
    focus_items = state["focus_items"]
    due_items = state["due_items"]
    upcoming_items = state["upcoming_7_items"]
    learned_items = state.get("learned_items", [])
    focus_label = "到期知识卡" if due_items else "未来 7 天知识卡"
    bulk_button = '<button class="inline-button" type="button" data-review-bulk>一键标记当前到期项已学习</button>' if due_items else ""
    bulk_button_line = f"          {bulk_button}\n" if bulk_button else ""
    writeback_hint = (
        "工作流启动时会自动检查本地写回服务；若按钮不可用，运行 <code>make review-server-ensure</code>。"
        if due_items
        else "当前没有到期项；未来 7 天知识卡可逐条提前标记。工作流启动时会自动检查本地写回服务。"
    )
    body = f"""
    <section class="grid">
      <div class="metric"><b>{summary['due_count']}</b><span>今日到期</span></div>
      <div class="metric"><b>{summary['overdue_count']}</b><span>已经逾期</span></div>
      <div class="metric"><b>{summary.get('learned_today_count', 0)}</b><span>今日已学习</span></div>
      <div class="metric"><b>{summary['upcoming_7_count']}</b><span>7 天内复习</span></div>

      <section class="panel wide">
        <h2>{focus_label}</h2>
        <div class="review-actions">
{bulk_button_line}          <span class="review-status" data-review-status aria-live="polite">{writeback_hint}</span>
        </div>
        {review_items_table(focus_items, out, 12)}
      </section>

      <section class="panel">
        <h2>复习节奏</h2>
        <ol class="steps">
          <li>先遮住知识卡正文，只回答表格里的主动回忆问题。</li>
          <li>再打开知识卡，核对一句话解释、误区和研究用法。</li>
          <li>学完后点击表格里的按钮；如果本页到期项都学完，可以点击“一键标记当前到期项已学习”。</li>
          <li>也可以直接对 Codex 说：<code>今天到期复习都学完了</code>。</li>
          <li>系统会写回 <code>review_queue.csv</code>，把条目移到“今日已学习”，并安排下一次复习。</li>
        </ol>
      </section>
      <section class="panel">
        <h2>源数据</h2>
        <div class="list">
          <div class="item"><a href="{href(REVIEW_QUEUE, out)}">review_queue.csv</a><div class="meta">长期复习队列源表。</div></div>
          <div class="item"><a href="{href(REVIEW_STATE, out)}">review_state.json</a><div class="meta">今日复习状态，供仪表盘和项目状态读取。</div></div>
        </div>
      </section>

      <section class="panel wide">
        <h2>今日已学习</h2>
        {review_items_table(learned_items, out, 20)}
      </section>

      <section class="panel wide">
        <h2>未来 7 天</h2>
        {review_items_table(upcoming_items, out, 20)}
      </section>
    </section>
    {review_mark_script()}
"""
    write_text_if_changed(out, shell("今日复习入口", "主动回忆、知识卡核对和下一轮阅读问题。", "复习", body, out))


def build_search_page() -> None:
    SEARCH_INDEX_HTML.parent.mkdir(parents=True, exist_ok=True)
    rows = artifact_manifest_rows()
    write_search_index(rows)
    state = build_search_index(rows)
    out = SEARCH_INDEX_HTML
    data_json = json.dumps(state, ensure_ascii=False).replace("</", "<\\/")
    layer_options = sorted({entry["layer"] for entry in state["entries"] if entry.get("layer")})
    type_options = sorted({entry["display_type"] for entry in state["entries"] if entry.get("display_type")})
    project_options = sorted({entry["project"] for entry in state["entries"] if entry.get("project")})
    layer_buttons = "".join(f'<button type="button" data-layer="{esc(layer)}">{esc(layer)}</button>' for layer in layer_options)
    type_options_html = "".join(f'<option value="{esc(kind)}">{esc(kind)}</option>' for kind in type_options)
    project_options_html = "".join(f'<option value="{esc(project)}">{esc(project)}</option>' for project in project_options)
    body = f"""
    <style>
      .search-box {{
        display: grid;
        gap: 12px;
      }}
      .search-box input, .search-box select {{
        min-height: 42px;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 8px 10px;
        font: inherit;
        background: #fff;
      }}
      .filter-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }}
      .filter-row button {{
        min-height: 44px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: #fff;
        padding: 6px 12px;
        font: inherit;
        cursor: pointer;
      }}
      .filter-row button.active {{
        border-color: var(--blue);
        color: var(--blue);
        background: #eef4ff;
      }}
      .result-row {{
        min-width: 0;
        border-left: 3px solid var(--blue);
        background: var(--soft);
        border-radius: 0 8px 8px 0;
        padding: 12px 14px;
        overflow-wrap: anywhere;
      }}
      .result-title {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: baseline;
        min-width: 0;
      }}
      .result-title a {{
        min-width: 0;
        overflow-wrap: anywhere;
      }}
      .badge {{
        display: inline-flex;
        align-items: center;
        max-width: 100%;
        border-radius: 999px;
        background: #eef3f8;
        border: 1px solid #d8e2ec;
        padding: 1px 7px;
        color: var(--muted);
        font-size: 12px;
      }}
      mark {{
        background: #fff0b8;
        color: inherit;
        border-radius: 3px;
        padding: 0 2px;
      }}
      .result-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 6px;
      }}
      .keyword {{
        display: inline-flex;
        max-width: 100%;
        border: 1px solid #d8e2ec;
        background: #fff;
        border-radius: 999px;
        padding: 1px 7px;
        color: var(--muted);
        font-size: 12px;
      }}
      .score {{
        color: var(--amber);
        font-weight: 700;
      }}
    </style>
    <section class="grid">
      <div class="metric"><b>{state['entry_count']}</b><span>可搜索入口</span></div>
      <div class="metric"><b>{len(layer_options)}</b><span>架构层</span></div>
      <div class="metric"><b>{len(type_options)}</b><span>展示类型</span></div>
      <div class="metric"><b id="visibleCount">0</b><span>当前结果</span></div>

      <section class="panel wide">
        <h2>全局搜索</h2>
        <div class="search-box">
          <input id="searchInput" type="search" placeholder="搜索论文题名、概念、方法、项目、日志、证据边界或文件路径">
          <div class="filter-row">
            <button type="button" data-layer="all" class="active">全部层</button>
            {layer_buttons}
            <select id="typeFilter" aria-label="展示类型">
              <option value="all">全部类型</option>
              {type_options_html}
            </select>
            <select id="projectFilter" aria-label="项目">
              <option value="all">全部项目</option>
              {project_options_html}
            </select>
            <select id="sortMode" aria-label="排序">
              <option value="relevance">相关度优先</option>
              <option value="recent">最近日期优先</option>
              <option value="weight">核心入口优先</option>
              <option value="title">标题 A-Z</option>
            </select>
          </div>
        </div>
      </section>

      <section class="panel wide">
        <h2>搜索结果</h2>
        <div id="searchResults" class="list"></div>
      </section>

      <section class="panel">
        <h2>使用方式</h2>
        <ol class="steps">
          <li>用中文关键词搜主题、论文、方法或项目文件。</li>
          <li>用架构层筛选源材料、知识资产或展示入口。</li>
          <li>用项目和类型过滤缩小范围，结果按相关度、日期或核心入口排序。</li>
          <li>点击结果进入 HTML 展示页，再回到图谱或复习页继续连接。</li>
        </ol>
      </section>
      <section class="panel">
        <h2>源数据</h2>
        <div class="list">
          <div class="item"><a href="{href(SEARCH_INDEX_JSON, out)}">search_index.json</a><div class="meta">由 artifact manifest 生成的搜索索引。</div></div>
          <div class="item"><a href="{href(ARTIFACT_MANIFEST, out)}">artifact_manifest.csv</a><div class="meta">搜索结果的展示路径来源。</div></div>
        </div>
      </section>
    </section>
    <script>
      const searchState = __SEARCH_JSON__;
      const rootPrefix = "../";
      const input = document.getElementById("searchInput");
      const results = document.getElementById("searchResults");
      const visibleCount = document.getElementById("visibleCount");
      const typeFilter = document.getElementById("typeFilter");
      const projectFilter = document.getElementById("projectFilter");
      const sortMode = document.getElementById("sortMode");
      const layerButtons = Array.from(document.querySelectorAll("[data-layer]"));
      let activeLayer = "all";

      function escapeHtml(value) {{
        return String(value).replace(/[&<>"']/g, (char) => ({{
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;"
        }}[char]));
      }}

      function hrefFor(displayPath) {{
        return rootPrefix + String(displayPath).split("/").map(encodeURIComponent).join("/");
      }}

      function escapeRegExp(value) {{
        return String(value).replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&");
      }}

      function highlight(value, tokens) {{
        let text = escapeHtml(value || "");
        tokens.filter((token) => token.length >= 2).slice(0, 8).forEach((token) => {{
          const pattern = new RegExp(escapeRegExp(escapeHtml(token)), "ig");
          text = text.replace(pattern, (match) => `<mark>${{match}}</mark>`);
        }});
        return text;
      }}

      function snippet(entry, tokens) {{
        const base = String(entry.snippet_text || entry.summary || entry.source_path || "");
        if (!tokens.length) return base.slice(0, 220);
        const lower = base.toLowerCase();
        let index = -1;
        for (const token of tokens) {{
          index = lower.indexOf(token);
          if (index >= 0) break;
        }}
        if (index < 0) return base.slice(0, 220);
        const start = Math.max(0, index - 80);
        const end = Math.min(base.length, index + 180);
        return `${{start > 0 ? "..." : ""}}${{base.slice(start, end)}}${{end < base.length ? "..." : ""}}`;
      }}

      function score(entry, tokens) {{
        if (!tokens.length) return Number(entry.weight || 0);
        const title = String(entry.title || "").toLowerCase();
        const summary = String(entry.summary || "").toLowerCase();
        const source = String(entry.source_path || "").toLowerCase();
        const keywords = (entry.keywords || []).join(" ").toLowerCase();
        let total = Number(entry.weight || 0);
        tokens.forEach((token) => {{
          if (title.includes(token)) total += 80;
          if (keywords.includes(token)) total += 50;
          if (summary.includes(token)) total += 25;
          if (source.includes(token)) total += 15;
          if (String(entry.search_text || "").includes(token)) total += 5;
        }});
        return total;
      }}

      function matches(entry, tokens) {{
        if (activeLayer !== "all" && entry.layer !== activeLayer) return false;
        if (typeFilter.value !== "all" && entry.display_type !== typeFilter.value) return false;
        if (projectFilter.value !== "all" && entry.project !== projectFilter.value) return false;
        return tokens.every((token) => entry.search_text.includes(token));
      }}

      function sortEntries(entries) {{
        if (sortMode.value === "recent") {{
          return entries.sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")) || b._score - a._score);
        }}
        if (sortMode.value === "weight") {{
          return entries.sort((a, b) => Number(b.weight || 0) - Number(a.weight || 0) || b._score - a._score);
        }}
        if (sortMode.value === "title") {{
          return entries.sort((a, b) => String(a.title || "").localeCompare(String(b.title || ""), "zh-Hans-CN"));
        }}
        return entries.sort((a, b) => b._score - a._score || String(b.date || "").localeCompare(String(a.date || "")));
      }}

      function render() {{
        const tokens = input.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);
        const visible = sortEntries(searchState.entries.filter((entry) => matches(entry, tokens)).map((entry) => ({{ ...entry, _score: score(entry, tokens) }}))).slice(0, 80);
        visibleCount.textContent = visible.length;
        if (!visible.length) {{
          results.innerHTML = '<div class="empty">没有匹配结果。换一个论文题名、概念、方法或项目关键词。</div>';
          return;
        }}
        results.innerHTML = visible.map((entry) => `
          <div class="result-row">
            <div class="result-title">
              <a href="${{hrefFor(entry.display_path)}}">${{highlight(entry.title, tokens)}}</a>
              <span class="badge">${{escapeHtml(entry.layer || "Unknown")}}</span>
              <span class="badge">${{escapeHtml(entry.display_type)}}</span>
              ${{entry.project ? `<span class="badge">${{escapeHtml(entry.project)}}</span>` : ""}}
              ${{entry.date ? `<span class="badge">${{escapeHtml(entry.date)}}</span>` : ""}}
              <span class="badge score">${{Math.round(entry._score)}}</span>
            </div>
            <div class="meta">${{highlight(snippet(entry, tokens), tokens)}}</div>
            <div class="result-meta">${{(entry.keywords || []).slice(0, 8).map((keyword) => `<span class="keyword">${{escapeHtml(keyword)}}</span>`).join("")}}</div>
            <div class="meta">源：${{escapeHtml(entry.source_path)}} · 展示：${{escapeHtml(entry.display_path)}}</div>
          </div>
        `).join("");
      }}

      layerButtons.forEach((button) => {{
        button.addEventListener("click", () => {{
          activeLayer = button.dataset.layer || "all";
          layerButtons.forEach((item) => item.classList.toggle("active", item === button));
          render();
        }});
      }});
      input.addEventListener("input", render);
      typeFilter.addEventListener("change", render);
      projectFilter.addEventListener("change", render);
      sortMode.addEventListener("change", render);
      render();
    </script>
"""
    body = body.replace("__SEARCH_JSON__", data_json)
    write_text_if_changed(out, shell("全局搜索入口", "搜索论文、知识卡、项目状态、日志和图谱展示资产。", "搜索", body, out))


def build_graph_index() -> None:
    KNOWLEDGE_GRAPH.mkdir(parents=True, exist_ok=True)
    out = KNOWLEDGE_GRAPH / "index.html"
    node_count, edge_count, _top_nodes = graph_counts()
    graph = graph_data()
    kind_counter = Counter(str(node.get("kind", "linked")) for node in graph["nodes"])
    graph_json = json.dumps(graph, ensure_ascii=False)
    body = """
    <style>
      .graph-panel { padding: 0; overflow: hidden; }
      .graph-intro {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 12px;
        padding: 18px;
        border-bottom: 1px solid var(--line);
      }
      .graph-intro p { max-width: 760px; margin: 0; color: var(--muted); }
      .graph-toolbar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        padding: 14px 18px;
        border-bottom: 1px solid var(--line);
        background: #fbfcfd;
      }
      .graph-toolbar input {
        flex: 1 1 240px;
        min-height: 38px;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 8px 10px;
        font: inherit;
      }
      .graph-toolbar button {
        min-height: 36px;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 6px 12px;
        background: #fff;
        color: var(--ink);
        font: inherit;
        cursor: pointer;
      }
      .graph-toolbar button.active {
        color: var(--blue);
        border-color: var(--blue);
        background: #eef4ff;
      }
      .graph-layout {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 310px;
        min-height: 660px;
      }
      .graph-canvas {
        border-right: 1px solid var(--line);
        background:
          radial-gradient(circle at 50% 48%, rgba(36, 99, 235, 0.09), transparent 30%),
          radial-gradient(circle at 16% 18%, rgba(22, 128, 93, 0.11), transparent 24%),
          linear-gradient(180deg, #ffffff 0%, #f5f8fb 100%);
      }
      #graphSvg {
        width: 100%;
        height: 660px;
        display: block;
      }
      .edge-line {
        stroke: #9aacbd;
        stroke-opacity: 0.38;
        stroke-width: 1.2;
      }
      .node-circle {
        cursor: pointer;
        stroke: #fff;
        stroke-width: 2.2;
        filter: drop-shadow(0 2px 3px rgba(20, 32, 44, 0.16));
      }
      .node-circle.selected {
        stroke: #182026;
        stroke-width: 3;
      }
      .node-label {
        fill: #182026;
        font-size: 12px;
        paint-order: stroke;
        stroke: #fff;
        stroke-width: 4px;
        stroke-linejoin: round;
        pointer-events: none;
      }
      .graph-side {
        padding: 18px;
        background: #fff;
      }
      .graph-side h2 { margin-bottom: 8px; }
      .node-pill {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 3px 8px;
        background: #eef4ff;
        color: var(--blue);
        font-size: 12px;
      }
      .neighbor-list {
        margin: 10px 0 0;
        padding-left: 18px;
        color: var(--muted);
      }
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
      }
      .legend span {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        color: var(--muted);
        font-size: 12px;
      }
      .legend i {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
      }
      @media (max-width: 900px) {
        .graph-layout { grid-template-columns: 1fr; }
        .graph-canvas { border-right: 0; border-bottom: 1px solid var(--line); }
        #graphSvg { height: 540px; }
      }
    </style>
    <section class="grid">
      <div class="metric"><b>{node_count}</b><span>节点</span></div>
      <div class="metric"><b>{edge_count}</b><span>关系边</span></div>
      <div class="metric"><b>{concept_count}</b><span>概念节点</span></div>
      <div class="metric"><b>{method_count}</b><span>方法节点</span></div>

      <section class="panel wide graph-panel">
        <div class="graph-intro">
          <div>
            <h2>关系图谱</h2>
            <p>节点越靠近中心，连接越密。优先看主读论文、核心概念、方法和项目之间的路径，而不是逐行查 CSV。</p>
          </div>
          <div class="legend">
            <span><i style="background:#2463eb"></i>文献</span>
            <span><i style="background:#16805d"></i>概念</span>
            <span><i style="background:#a15c07"></i>方法</span>
            <span><i style="background:#b4234b"></i>项目</span>
            <span><i style="background:#607086"></i>关联节点</span>
          </div>
        </div>
        <div class="graph-toolbar">
          <input id="graphSearch" type="search" placeholder="搜索论文、概念、方法或项目节点">
          <button type="button" data-kind="all">全部</button>
          <button type="button" data-kind="project_scope" class="active">只看主项目</button>
          <button type="button" data-kind="core_chain">论文-概念-方法主链</button>
          <button type="button" data-kind="literature">文献</button>
          <button type="button" data-kind="concept">概念</button>
          <button type="button" data-kind="method">方法</button>
          <button type="button" data-kind="project">项目</button>
          <button type="button" data-kind="linked">其他关联</button>
        </div>
        <div class="graph-layout">
          <div class="graph-canvas">
            <svg id="graphSvg" viewBox="0 0 1200 720" role="img" aria-label="知识图谱可视化"></svg>
          </div>
          <aside class="graph-side">
            <p id="graphStats" class="meta"></p>
            <div id="nodeInfo">
              <h2>点击一个节点</h2>
              <p class="meta">查看它连接了哪些论文、概念、方法或项目。</p>
            </div>
          </aside>
        </div>
      </section>

      <section class="panel">
        <h2>图谱源文件</h2>
        <div class="list">
          <div class="item"><a href="{nodes_href}">obsidian_nodes.csv</a><div class="meta">节点源数据，供核对或导出。</div></div>
          <div class="item"><a href="{edges_href}">obsidian_edges.csv</a><div class="meta">关系边源数据，供核对或导出。</div></div>
          <div class="item"><a href="{index_href}">knowledge_index.csv</a><div class="meta">知识卡索引。</div></div>
          <div class="item"><a href="{manifest_href}">artifact_manifest.csv</a><div class="meta">源资产到 HTML 展示页的映射清单。</div></div>
        </div>
      </section>
      <section class="panel">
        <h2>读图顺序</h2>
        <ol class="steps">
          <li>先搜索今天论文或当前项目，看它连接到哪些概念与方法。</li>
          <li>再点核心概念，看它同时服务哪些论文和研究问题。</li>
          <li>最后把薄弱路径转成下一轮阅读或写作问题。</li>
        </ol>
      </section>
    </section>
    <script>
      const graphData = __GRAPH_JSON__;
      const svg = document.getElementById("graphSvg");
      const search = document.getElementById("graphSearch");
      const info = document.getElementById("nodeInfo");
      const stats = document.getElementById("graphStats");
      const buttons = Array.from(document.querySelectorAll("[data-kind]"));
      const nodeMap = new Map(graphData.nodes.map((node) => [node.id, node]));
      const mainProjectId = "{esc(ACTIVE_PROJECT)}";
      const coreKinds = new Set(["literature", "concept", "method", "project"]);
      const palette = {
        literature: "#2463eb",
        concept: "#16805d",
        method: "#a15c07",
        project: "#b4234b",
        learning: "#7c3aed",
        linked: "#607086"
      };
      const kindLabel = {
        literature: "文献",
        concept: "概念",
        method: "方法",
        project: "项目",
        learning: "学习记录",
        linked: "关联节点"
      };
      let activeKind = "project_scope";
      let selectedId = null;

      function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, (char) => ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;"
        }[char]));
      }

      function svgElement(name, attrs) {
        const element = document.createElementNS("http://www.w3.org/2000/svg", name);
        Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
        return element;
      }

      function nodesForActiveMode() {
        if (activeKind === "project_scope") {
          const keep = new Set([mainProjectId]);
          graphData.edges.forEach((edge) => {
            if (edge.source === mainProjectId) keep.add(edge.target);
            if (edge.target === mainProjectId) keep.add(edge.source);
          });
          return graphData.nodes.filter((node) => keep.has(node.id) && (node.id === mainProjectId || coreKinds.has(node.kind)));
        }
        if (activeKind === "core_chain") {
          const keep = new Set();
          graphData.edges.forEach((edge) => {
            const source = nodeMap.get(edge.source);
            const target = nodeMap.get(edge.target);
            if (source && target && coreKinds.has(source.kind) && coreKinds.has(target.kind)) {
              keep.add(edge.source);
              keep.add(edge.target);
            }
          });
          return graphData.nodes.filter((node) => keep.has(node.id));
        }
        return graphData.nodes.filter((node) => activeKind === "all" || node.kind === activeKind);
      }

      function visibleNodes() {
        const query = search.value.trim().toLowerCase();
        const base = nodesForActiveMode();
        if (!query) return base;
        const direct = base.filter((node) => `${node.label} ${node.id} ${node.type}`.toLowerCase().includes(query));
        const keep = new Set(direct.map((node) => node.id));
        graphData.edges.forEach((edge) => {
          if (keep.has(edge.source)) keep.add(edge.target);
          if (keep.has(edge.target)) keep.add(edge.source);
        });
        return base.filter((node) => keep.has(node.id));
      }

      function layout(nodes) {
        const sorted = [...nodes].sort((a, b) => (b.degree || 0) - (a.degree || 0));
        const rings = [sorted.slice(0, 1), sorted.slice(1, 12), sorted.slice(12, 38), sorted.slice(38)];
        const radii = [0, 170, 305, 435];
        const positions = new Map();
        rings.forEach((ring, ringIndex) => {
          const radius = radii[ringIndex];
          ring.forEach((node, index) => {
            const angle = ring.length === 1
              ? -Math.PI / 2
              : -Math.PI / 2 + (index * Math.PI * 2 / ring.length) + ringIndex * 0.2;
            positions.set(node.id, {
              x: 600 + Math.cos(angle) * radius,
              y: 360 + Math.sin(angle) * radius * 0.72
            });
          });
        });
        return positions;
      }

      function showNode(nodeId) {
        const node = nodeMap.get(nodeId);
        if (!node) return;
        selectedId = nodeId;
        const relatedEdges = graphData.edges.filter((edge) => edge.source === nodeId || edge.target === nodeId);
        const neighbors = relatedEdges
          .map((edge) => nodeMap.get(edge.source === nodeId ? edge.target : edge.source))
          .filter(Boolean)
          .sort((a, b) => (b.degree || 0) - (a.degree || 0));
        const neighborList = neighbors.slice(0, 14).map((neighbor) =>
          `<li>${escapeHtml(neighbor.label)} <span class="meta">(${escapeHtml(kindLabel[neighbor.kind] || neighbor.kind)})</span></li>`
        ).join("");
        info.innerHTML = `
          <h2>${escapeHtml(node.label)}</h2>
          <p><span class="node-pill">${escapeHtml(kindLabel[node.kind] || node.kind)}</span></p>
          <p class="meta">源类型：${escapeHtml(node.type)} · 连接数：${escapeHtml(node.degree || 0)}</p>
          <h3>相邻节点</h3>
          ${neighborList ? `<ol class="neighbor-list">${neighborList}</ol>` : '<p class="meta">暂无相邻节点。</p>'}
        `;
        render();
      }

      function render() {
        const nodes = visibleNodes();
        const visible = new Set(nodes.map((node) => node.id));
        const edges = graphData.edges.filter((edge) => visible.has(edge.source) && visible.has(edge.target));
        const positions = layout(nodes);
        svg.innerHTML = "";
        stats.textContent = `${nodes.length} 个可见节点 · ${edges.length} 条可见关系`;

        edges.forEach((edge) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return;
          const line = svgElement("line", {
            x1: source.x,
            y1: source.y,
            x2: target.x,
            y2: target.y,
            class: "edge-line"
          });
          svg.appendChild(line);
        });

        nodes.forEach((node, index) => {
          const pos = positions.get(node.id);
          if (!pos) return;
          const radius = Math.max(8, Math.min(26, 7 + Math.sqrt(node.degree || 1) * 3));
          const group = svgElement("g", { tabindex: "0", role: "button", "aria-label": node.label });
          const circle = svgElement("circle", {
            cx: pos.x,
            cy: pos.y,
            r: radius,
            fill: palette[node.kind] || palette.linked,
            class: `node-circle${node.id === selectedId ? " selected" : ""}`
          });
          const title = svgElement("title", {});
          title.textContent = `${node.label} · ${kindLabel[node.kind] || node.kind} · ${node.degree || 0} links`;
          group.appendChild(circle);
          group.appendChild(title);

          const query = search.value.trim();
          if (index < 32 || node.degree >= 6 || query) {
            const label = svgElement("text", {
              x: pos.x,
              y: pos.y + radius + 14,
              "text-anchor": "middle",
              class: "node-label"
            });
            label.textContent = node.label.length > 18 ? `${node.label.slice(0, 18)}…` : node.label;
            group.appendChild(label);
          }

          group.addEventListener("click", () => showNode(node.id));
          group.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") showNode(node.id);
          });
          svg.appendChild(group);
        });
      }

      buttons.forEach((button) => {
        button.addEventListener("click", () => {
          activeKind = button.dataset.kind || "all";
          buttons.forEach((item) => item.classList.toggle("active", item === button));
          render();
        });
      });
      search.addEventListener("input", () => render());
      if (graphData.nodes.length) {
        selectedId = graphData.nodes[0].id;
        showNode(selectedId);
      } else {
        render();
      }
    </script>
"""
    body = (
        body.replace("{node_count}", str(node_count))
        .replace("{edge_count}", str(edge_count))
        .replace("{concept_count}", str(kind_counter.get("concept", 0)))
        .replace("{method_count}", str(kind_counter.get("method", 0)))
        .replace("{nodes_href}", href(GRAPH_DIR / "obsidian_nodes.csv", out))
        .replace("{edges_href}", href(GRAPH_DIR / "obsidian_edges.csv", out))
        .replace("{index_href}", href(GRAPH_DIR / "knowledge_index.csv", out))
        .replace("{manifest_href}", href(ARTIFACT_MANIFEST, out))
        .replace("__GRAPH_JSON__", graph_json)
    )
    write_text_if_changed(out, shell("知识图谱入口", "查看知识节点、关系边和高连接主题。", "知识图谱", body, out))


def main() -> int:
    PAPER_READING.mkdir(parents=True, exist_ok=True)
    PAPER_VIEWS.mkdir(parents=True, exist_ok=True)
    DIR_VIEWS.mkdir(parents=True, exist_ok=True)
    HTML_LOGS.mkdir(parents=True, exist_ok=True)
    LOG_VIEWS.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_CARDS.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_CARD_VIEWS.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_GRAPH.mkdir(parents=True, exist_ok=True)
    SEARCH_INDEX_HTML.parent.mkdir(parents=True, exist_ok=True)
    build_markdown_views()
    rewrite_paper_markdown_links()
    build_knowledge_card_views()
    build_log_views()
    build_directory_views()
    build_paper_today()
    build_paper_index()
    build_logs_index()
    build_review_today()
    build_cards_index()
    build_graph_index()
    write_collaboration_state()
    write_archive_policy()
    build_dashboard()
    build_artifact_manifest()
    build_search_page()
    build_artifact_manifest()
    print(f"Wrote {ROOT / 'study_dashboard.html'}")
    print(f"Wrote {PAPER_READING / 'today.html'}")
    print(f"Wrote {PAPER_READING / 'index.html'}")
    print(f"Wrote {PAPER_VIEWS}")
    print(f"Wrote {DIR_VIEWS}")
    print(f"Wrote {KNOWLEDGE_CARDS / 'index.html'}")
    print(f"Wrote {REVIEW_TODAY}")
    print(f"Wrote {REVIEW_STATE}")
    print(f"Wrote {KNOWLEDGE_CARD_VIEWS}")
    print(f"Wrote {KNOWLEDGE_GRAPH / 'index.html'}")
    print(f"Wrote {SEARCH_INDEX_HTML}")
    print(f"Wrote {SEARCH_INDEX_JSON}")
    print(f"Wrote {ARTIFACT_MANIFEST}")
    print(f"Wrote {COLLABORATION_HTML}")
    print(f"Wrote {ARCHIVE_POLICY_HTML}")
    print(f"Wrote {HTML_LOGS / 'index.html'}")
    print(f"Wrote {LOG_VIEWS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
