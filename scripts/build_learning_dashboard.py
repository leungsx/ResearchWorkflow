#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote, unquote


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
PAPER_READING = ROOT / "paper_reading"
HTML_LOGS = ROOT / "logs"
KNOWLEDGE_CARDS = ROOT / "knowledge_cards"
KNOWLEDGE_GRAPH = ROOT / "knowledge_graph"
PAPER_VIEWS = PAPER_READING / "views"
KNOWLEDGE_CARD_VIEWS = KNOWLEDGE_CARDS / "views"
LOG_VIEWS = HTML_LOGS / "views"
WORKFLOW_HEALTH = ROOT / "workflow_health.html"
BACKUP_INDEX = ROOT / "backups" / "index.html"
PAPER_RESERVED = {"index.html", "today.html"}

CONCEPTS = VAULT / "02_Concepts"
METHODS = VAULT / "03_Methods"
LEARNING_SESSIONS = VAULT / "12_Learning_Log" / "sessions"
GRAPH_DIR = VAULT / "13_Knowledge_Graph"
REVIEW_QUEUE = VAULT / "14_Review_Queue" / "review_queue.csv"

MARKDOWN_VIEW_SOURCES = [
    (
        "vault-home",
        "Vault 首页",
        VAULT / "Home.md",
        "Obsidian Home 的浏览器友好镜像页。",
    ),
    (
        "cnki_2023_34348faa1e-note",
        "Obsidian 论文笔记",
        VAULT / "01_Literature" / "cnki_2023_34348faa1e.md",
        "今日主读论文的 Obsidian 源笔记浏览版。",
    ),
    (
        "cnki_2023_34348faa1e-reader",
        "Source-Grounded Reader",
        ROOT / "projects" / "library_short_video" / "literature" / "readers" / "cnki_2023_34348faa1e" / "paper.md",
        "按证据块组织的 Reader 浏览版。",
    ),
    (
        "literature_review_workbench",
        "文献综述工作台",
        ROOT / "projects" / "library_short_video" / "literature" / "literature_review_workbench.md",
        "图书馆短视频项目的文献综述工作台浏览版。",
    ),
    (
        "literature_synthesis",
        "跨文献综述",
        ROOT / "projects" / "library_short_video" / "03_literature_synthesis.md",
        "当前项目跨文献综合与证据边界浏览版。",
    ),
    (
        "sicas-model-concept",
        "知识卡：SICAS 模型",
        VAULT / "02_Concepts" / "SICAS模型.md",
        "今日主读论文沉淀出的核心概念卡浏览版。",
    ),
    (
        "dci-index-method",
        "方法卡：DCI 传播力指数",
        VAULT / "03_Methods" / "DCI传播力指数.md",
        "今日主读论文沉淀出的传播力指标方法卡浏览版。",
    ),
    (
        "innovation_limitation_bank",
        "创新-局限-机会台账",
        ROOT / "projects" / "library_short_video" / "literature" / "innovation_limitation_bank.md",
        "当前项目创新、局限与后续机会的浏览版。",
    ),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def href(target: Path, from_file: Path) -> str:
    rel = os.path.relpath(target, from_file.parent).replace(os.sep, "/")
    return quote(rel, safe="/#:.?=&%-_")


def read_text(path: Path, limit: int = 20000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except FileNotFoundError:
        return ""


def md_title(path: Path) -> str:
    text = read_text(path, limit=8000)
    frontmatter_title = re.search(r"(?m)^title:\s*\"?(.+?)\"?\s*$", text)
    if frontmatter_title:
        return frontmatter_title.group(1).strip().strip('"')
    heading = re.search(r"(?m)^#\s+(.+)$", text)
    if heading:
        return heading.group(1).strip()
    return path.stem


def html_title(path: Path) -> str:
    text = read_text(path, limit=4000)
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
    if title:
        return re.sub(r"\s+", " ", title.group(1)).strip()
    heading = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", text)
    if heading:
        return re.sub(r"<[^>]+>", "", heading.group(1)).strip()
    return path.stem


def list_html(directory: Path, exclude: set[str] | None = None) -> list[Path]:
    if not directory.exists():
        return []
    excluded = {"index.html"}
    if exclude:
        excluded |= exclude
    return sorted(
        [p for p in directory.glob("*.html") if p.name not in excluded],
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )


def list_md(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        [p for p in directory.glob("*.md") if p.is_file()],
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )


def latest_file(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern), key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
    return files[0] if files else None


def paper_pages() -> list[Path]:
    return list_html(PAPER_READING, exclude=PAPER_RESERVED)


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def due_reviews() -> list[dict[str, str]]:
    today = dt.date.today().isoformat()
    rows = csv_rows(REVIEW_QUEUE)
    due: list[dict[str, str]] = []
    for row in rows:
        next_review = row.get("next_review", "")
        if next_review and next_review <= today:
            due.append(row)
    return due


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
      --ink: #182026;
      --muted: #61707d;
      --line: #d9e0e6;
      --paper: #ffffff;
      --soft: #f6f8fa;
      --blue: #2463eb;
      --green: #16805d;
      --amber: #a15c07;
      --rose: #b4234b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", Arial, sans-serif;
      color: var(--ink);
      background: #f4f6f8;
      line-height: 1.55;
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
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .sub { color: var(--muted); max-width: 780px; }
    .nav { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
    .nav a {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font-size: 14px;
    }
    main.wrap { padding-top: 22px; }
    .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 14px; }
    .panel {
      grid-column: span 6;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .panel.wide { grid-column: 1 / -1; }
    .metric {
      grid-column: span 3;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .metric b { display: block; font-size: 28px; line-height: 1.1; }
    .metric span { color: var(--muted); font-size: 13px; }
    .list { display: grid; gap: 10px; }
    .item {
      border-left: 3px solid var(--blue);
      background: var(--soft);
      padding: 10px 12px;
      border-radius: 0 7px 7px 0;
    }
    .item.green { border-left-color: var(--green); }
    .item.amber { border-left-color: var(--amber); }
    .item.rose { border-left-color: var(--rose); }
    .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
    .empty {
      color: var(--muted);
      background: var(--soft);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .steps { margin: 0; padding-left: 20px; }
    .steps li { margin: 6px 0; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { text-align: left; border-bottom: 1px solid var(--line); padding: 8px 6px; vertical-align: top; }
    th { color: var(--muted); font-weight: 600; }
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
      min-height: 34px;
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      font-size: 14px;
      cursor: pointer;
    }
    .toolbar button.active {
      border-color: var(--blue);
      color: var(--blue);
      background: #eef4ff;
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
      h1 { font-size: 28px; }
    }
    """


def shell(title: str, subtitle: str, current: str, body: str, output: Path) -> str:
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    nav = [
        ("总览", ROOT / "study_dashboard.html"),
        ("今日精读", PAPER_READING / "today.html"),
        ("论文归档", PAPER_READING / "index.html"),
        ("知识卡", KNOWLEDGE_CARDS / "index.html"),
        ("知识图谱", KNOWLEDGE_GRAPH / "index.html"),
        ("学习日志", HTML_LOGS / "index.html"),
        ("工作流体检", WORKFLOW_HEALTH),
        ("Vault 首页", PAPER_VIEWS / "vault-home.html"),
    ]
    nav_items: list[str] = []
    for label, path in nav:
        current_attr = ' aria-current="page"' if label == current else ""
        nav_items.append(f'<a href="{href(path, output)}"{current_attr}>{esc(label)}</a>')
    nav_html = "\n".join(nav_items)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>{common_css()}</style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>{esc(title)}</h1>
      <p class="sub">{esc(subtitle)}</p>
      <nav class="nav">{nav_html}</nav>
    </div>
  </header>
  <main class="wrap">
{body}
  </main>
  <footer class="wrap">Generated by scripts/build_learning_dashboard.py at {esc(generated)}.</footer>
</body>
</html>
"""


def card_view_path(source: Path) -> Path:
    rel = source.relative_to(ROOT)
    prefix = "concept" if source.parent == CONCEPTS else "method" if source.parent == METHODS else "card"
    ascii_stem = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-")
    digest = hashlib.sha1(str(rel).encode("utf-8")).hexdigest()[:8]
    slug = f"{ascii_stem}-{digest}" if ascii_stem else digest
    return KNOWLEDGE_CARD_VIEWS / f"{prefix}-{slug}.html"


def log_view_path(source: Path) -> Path:
    rel = source.relative_to(ROOT)
    ascii_stem = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-")
    digest = hashlib.sha1(str(rel).encode("utf-8")).hexdigest()[:8]
    slug = f"{ascii_stem}-{digest}" if ascii_stem else digest
    return LOG_VIEWS / f"{slug}.html"


def display_href(path: Path, output: Path) -> str:
    if path.suffix == ".md" and path.parent in {CONCEPTS, METHODS}:
        return href(card_view_path(path), output)
    if path.suffix == ".md" and path.parent == LEARNING_SESSIONS:
        return href(log_view_path(path), output)
    return href(path, output)


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
    today_panel = (
        f"""
      <section class="panel wide">
        <h2>固定入口</h2>
        <p>以后每天只点同一个入口即可：<a href="{href(today_entry, out)}">今日精读入口</a>。</p>
        <p>当前会打开：<strong>{esc(html_title(latest))}</strong></p>
      </section>
"""
        if latest
        else f"""
      <section class="panel wide">
        <h2>固定入口</h2>
        <div class="empty">固定入口已预留在 <a href="{href(today_entry, out)}">paper_reading/today.html</a>，但当前还没有可打开的精读页。</div>
      </section>
"""
    )
    body = f"""
    <section class="grid">
      <div class="metric"><b>{len(pages)}</b><span>论文精读 HTML</span></div>
      <div class="metric"><b>{len(concepts) + len(methods)}</b><span>概念/方法知识卡</span></div>
      <div class="metric"><b>{node_count}/{edge_count}</b><span>图谱节点/关系边</span></div>
      <div class="metric"><b>{len(due)}</b><span>今日应复习</span></div>

      {today_panel}

      <section class="panel wide">
        <h2>系统健康与备份</h2>
        <div class="list">
          <div class="item"><a href="{href(WORKFLOW_HEALTH, out)}">工作流体检页</a><div class="meta">检查入口、链接、镜像页、图谱、归档、复习队列和备份。</div></div>
          <div class="item green">{f'<a href="{href(BACKUP_INDEX, out)}">备份索引</a>' if BACKUP_INDEX.exists() else '备份索引'}<div class="meta">{esc(latest_backup.name if latest_backup else '尚未生成备份；运行 make workflow-backup。')}</div></div>
          <div class="item amber"><a href="{href(WORKFLOW_HEALTH, out)}">最近审计概览</a><div class="meta">{esc(str(latest_audit.relative_to(ROOT)) if latest_audit else '运行 make workflow-audit 后生成。')}</div></div>
          <div class="item rose">最近文件归类清单<div class="meta">{esc(str(latest_sweep.relative_to(ROOT)) if latest_sweep else '运行 make codex-sweep 后生成。')}</div></div>
        </div>
      </section>

      <section class="panel wide">
        <h2>今日使用顺序</h2>
        <ol class="steps">
          <li>早上从固定入口 <code>paper_reading/today.html</code> 进入，直接打开当天主读页。</li>
          <li>顺着页面进入新建/更新的概念卡、方法卡和来源论文笔记。</li>
          <li>打开知识图谱入口，查看这篇论文带来的新关系。</li>
          <li>晚上查看学习日志入口，确认归档、复习问题和明日行动。</li>
        </ol>
      </section>

      <section class="panel">
        <h2>最近论文精读</h2>
        {item_list(pages, out, "green")}
      </section>
      <section class="panel">
        <h2>最近学习日志</h2>
        {item_list(log_pages, out, "amber")}
      </section>
      <section class="panel">
        <h2>最近知识卡</h2>
        {item_list((concepts + methods)[:12], out, "rose")}
      </section>
      <section class="panel">
        <h2>图谱高连接节点</h2>
        {top_nodes_table(top_nodes)}
      </section>
    </section>
"""
    out.write_text(shell("ResearchWorkflow 学习仪表盘", "论文精读、知识卡、知识图谱和学习日志的统一入口。", "总览", body, out), encoding="utf-8")


def top_nodes_table(top_nodes: list[tuple[str, int]]) -> str:
    if not top_nodes:
        return '<div class="empty">暂无图谱关系。运行 make obsidian-graph 后会显示高连接节点。</div>'
    rows = "\n".join(f"<tr><td>{esc(name)}</td><td>{count}</td></tr>" for name, count in top_nodes)
    return f"<table><thead><tr><th>节点</th><th>连接数</th></tr></thead><tbody>{rows}</tbody></table>"


def render_inline_markdown(text: str) -> str:
    value = esc(text)
    value = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", value)
    value = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", lambda m: f'<span class="wikilink">{m.group(2)}</span>', value)
    value = re.sub(r"\[\[([^\]]+)\]\]", lambda m: f'<span class="wikilink">{m.group(1)}</span>', value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', value)
    return value


def strip_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if not match:
        return "", text
    return match.group(1).strip(), text[match.end() :]


def frontmatter_table(frontmatter: str) -> str:
    if not frontmatter:
        return ""
    rows: list[str] = []
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        rows.append(f"<tr><th>{esc(key.strip())}</th><td>{render_inline_markdown(value.strip())}</td></tr>")
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


def table_to_html(lines: list[str]) -> str:
    if len(lines) < 2:
        return ""
    headers = split_table_row(lines[0])
    body_rows = [split_table_row(line) for line in lines[2:]]
    head = "".join(f"<th>{render_inline_markdown(cell)}</th>" for cell in headers)
    body = []
    for row in body_rows:
        padded = row + [""] * max(0, len(headers) - len(row))
        body.append("<tr>" + "".join(f"<td>{render_inline_markdown(cell)}</td>" for cell in padded[: len(headers)]) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_markdown(text: str) -> str:
    frontmatter, body = strip_frontmatter(text)
    lines = body.splitlines()
    parts: list[str] = [frontmatter_table(frontmatter)] if frontmatter else []
    paragraph: list[str] = []
    list_kind: str | None = None
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{render_inline_markdown(' '.join(paragraph))}</p>")
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
            parts.append(table_to_html(table_lines))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)), 6)
            parts.append(f"<h{level}>{render_inline_markdown(heading.group(2))}</h{level}>")
            i += 1
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            flush_paragraph()
            flush_list()
            parts.append(f"<blockquote>{render_inline_markdown(quote.group(1))}</blockquote>")
            i += 1
            continue

        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        if unordered:
            flush_paragraph()
            if list_kind != "ul":
                flush_list()
                parts.append("<ul>")
                list_kind = "ul"
            parts.append(f"<li>{render_inline_markdown(unordered.group(1))}</li>")
            i += 1
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            if list_kind != "ol":
                flush_list()
                parts.append("<ol>")
                list_kind = "ol"
            parts.append(f"<li>{render_inline_markdown(ordered.group(1))}</li>")
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    flush_list()
    return "\n".join(part for part in parts if part)


def relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def configured_paper_view(source: Path) -> tuple[str, str, str] | None:
    resolved = source.resolve()
    for slug, title, configured_source, subtitle in MARKDOWN_VIEW_SOURCES:
        if configured_source.resolve() == resolved:
            return slug, title, subtitle
    return None


def generic_markdown_slug(source: Path) -> str:
    rel = relative_label(source)
    ascii_stem = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-")
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_stem}-{digest}" if ascii_stem else f"markdown-{digest}"


def paper_markdown_view_path(source: Path) -> Path:
    configured = configured_paper_view(source)
    slug = configured[0] if configured else generic_markdown_slug(source)
    return PAPER_VIEWS / f"{slug}.html"


def paper_markdown_view_title(source: Path) -> str:
    configured = configured_paper_view(source)
    if configured:
        return configured[1]
    return md_title(source) if source.exists() else source.stem


def paper_markdown_view_subtitle(source: Path) -> str:
    configured = configured_paper_view(source)
    if configured:
        return configured[2]
    return f"{relative_label(source)} 的浏览器友好镜像页。"


def local_markdown_source(page: Path, link: str) -> Path | None:
    base = link.split("#", 1)[0].split("?", 1)[0]
    if not base or "://" in base or base.startswith(("mailto:", "obsidian:")) or not base.endswith(".md"):
        return None
    source = (page.parent / unquote(base)).resolve()
    try:
        source.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return source


def markdown_sources_from_paper_pages() -> list[Path]:
    sources: dict[Path, Path] = {source.resolve(): source for _, _, source, _ in MARKDOWN_VIEW_SOURCES}
    href_pattern = re.compile(r'href=(["\'])([^"\']+?\.md(?:#[^"\']*)?)\1')
    for page in paper_pages():
        text = read_text(page, limit=1_000_000)
        for match in href_pattern.finditer(text):
            source = local_markdown_source(page, html.unescape(match.group(2)))
            if source:
                sources[source.resolve()] = source
    return sorted(sources.values(), key=relative_label)


def rewrite_paper_markdown_links() -> None:
    sources = {source.resolve(): paper_markdown_view_path(source) for source in markdown_sources_from_paper_pages()}
    href_pattern = re.compile(r'href=(["\'])([^"\']+?\.md(?:#[^"\']*)?)\1')
    for page in paper_pages():
        text = page.read_text(encoding="utf-8", errors="ignore")

        def replace(match: re.Match[str]) -> str:
            quote_char = match.group(1)
            source = local_markdown_source(page, html.unescape(match.group(2)))
            if not source:
                return match.group(0)
            view = sources.get(source.resolve())
            if not view:
                return match.group(0)
            return f"href={quote_char}{href(view, page)}{quote_char}"

        rewritten = href_pattern.sub(replace, text)
        if rewritten != text:
            page.write_text(rewritten, encoding="utf-8")


def build_markdown_views() -> None:
    PAPER_VIEWS.mkdir(parents=True, exist_ok=True)
    for source in markdown_sources_from_paper_pages():
        out = paper_markdown_view_path(source)
        title = paper_markdown_view_title(source)
        subtitle = paper_markdown_view_subtitle(source)
        if source.exists():
            article = render_markdown(source.read_text(encoding="utf-8", errors="ignore"))
            body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(source, out)}">打开原始 Markdown</a>
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
        out.write_text(shell(title, subtitle, "今日精读", body, out), encoding="utf-8")


def build_knowledge_card_views() -> None:
    KNOWLEDGE_CARD_VIEWS.mkdir(parents=True, exist_ok=True)
    for source in [*list_md(CONCEPTS), *list_md(METHODS)]:
        out = card_view_path(source)
        card_type = "概念卡" if source.parent == CONCEPTS else "方法卡"
        article = render_markdown(source.read_text(encoding="utf-8", errors="ignore"))
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(KNOWLEDGE_CARDS / 'index.html', out)}">返回知识卡入口</a>
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(source, out)}">打开原始 Markdown</a>
          <a href="{href(KNOWLEDGE_GRAPH / 'index.html', out)}">查看知识图谱</a>
        </div>
        <div class="source-path">源文件：{esc(source.relative_to(ROOT))}</div>
        <article class="md-view">
{article}
        </article>
      </section>
    </section>
"""
        out.write_text(shell(f"{card_type}：{md_title(source)}", "可直接在浏览器阅读的知识卡镜像页。", "知识卡", body, out), encoding="utf-8")


def build_log_views() -> None:
    LOG_VIEWS.mkdir(parents=True, exist_ok=True)
    for source in list_md(LEARNING_SESSIONS):
        out = log_view_path(source)
        article = render_markdown(source.read_text(encoding="utf-8", errors="ignore"))
        body = f"""
    <section class="grid">
      <section class="panel wide">
        <div class="toolbar">
          <a href="{href(HTML_LOGS / 'index.html', out)}">返回学习日志入口</a>
          <a href="{href(PAPER_READING / 'today.html', out)}">返回今日精读</a>
          <a href="{href(source, out)}">打开原始 Markdown</a>
          <a href="{href(KNOWLEDGE_GRAPH / 'index.html', out)}">查看知识图谱</a>
        </div>
        <div class="source-path">源文件：{esc(source.relative_to(ROOT))}</div>
        <article class="md-view">
{article}
        </article>
      </section>
    </section>
"""
        out.write_text(shell(f"学习日志：{md_title(source)}", "可直接在浏览器阅读的学习会话镜像页。", "学习日志", body, out), encoding="utf-8")


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
    out.write_text(shell(title, subtitle, "今日精读", body, out), encoding="utf-8")


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
    out.write_text(shell("论文精读归档", "固定入口请用 today.html；这里保留历史时间线。", "论文归档", body, out), encoding="utf-8")


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
    out.write_text(shell("学习日志入口", "每日学习记录、归档摘要和明日行动。", "学习日志", body, out), encoding="utf-8")


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
        {due_table}
      </section>
    </section>
"""
    out.write_text(shell("知识卡入口", "概念、方法、复习问题和与论文的连接。", "知识卡", body, out), encoding="utf-8")


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
          <button type="button" data-kind="all" class="active">全部</button>
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
      let activeKind = "all";
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

      function visibleNodes() {
        const query = search.value.trim().toLowerCase();
        const base = graphData.nodes.filter((node) => activeKind === "all" || node.kind === activeKind);
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
        .replace("__GRAPH_JSON__", graph_json)
    )
    out.write_text(shell("知识图谱入口", "查看知识节点、关系边和高连接主题。", "知识图谱", body, out), encoding="utf-8")


def main() -> int:
    PAPER_READING.mkdir(parents=True, exist_ok=True)
    PAPER_VIEWS.mkdir(parents=True, exist_ok=True)
    HTML_LOGS.mkdir(parents=True, exist_ok=True)
    LOG_VIEWS.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_CARDS.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_CARD_VIEWS.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_GRAPH.mkdir(parents=True, exist_ok=True)
    build_markdown_views()
    rewrite_paper_markdown_links()
    build_knowledge_card_views()
    build_log_views()
    build_paper_today()
    build_paper_index()
    build_logs_index()
    build_cards_index()
    build_graph_index()
    build_dashboard()
    print(f"Wrote {ROOT / 'study_dashboard.html'}")
    print(f"Wrote {PAPER_READING / 'today.html'}")
    print(f"Wrote {PAPER_READING / 'index.html'}")
    print(f"Wrote {PAPER_VIEWS}")
    print(f"Wrote {KNOWLEDGE_CARDS / 'index.html'}")
    print(f"Wrote {KNOWLEDGE_CARD_VIEWS}")
    print(f"Wrote {KNOWLEDGE_GRAPH / 'index.html'}")
    print(f"Wrote {HTML_LOGS / 'index.html'}")
    print(f"Wrote {LOG_VIEWS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
