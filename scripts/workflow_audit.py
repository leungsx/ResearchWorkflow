#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import os
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
PAPER_READING = ROOT / "paper_reading"
KNOWLEDGE_CARDS = ROOT / "knowledge_cards"
KNOWLEDGE_GRAPH = ROOT / "knowledge_graph"
HTML_LOGS = ROOT / "logs"
GRAPH_DIR = VAULT / "13_Knowledge_Graph"
REVIEW_QUEUE = VAULT / "14_Review_Queue" / "review_queue.csv"
AUDIT_DIR = VAULT / "07_Codex_Logs" / "workflow_audits"
COMPACT_DIR = VAULT / "07_Codex_Logs" / "compact_daily"
DAILY_DIR = VAULT / "07_Codex_Logs" / "daily"
SWEEP_DIR = VAULT / "07_Codex_Logs" / "file_sweeps"
PACK_DIR = VAULT / "09_Context_Packs"
BACKUP_DIR = ROOT / "backups"
HEALTH_HTML = ROOT / "workflow_health.html"


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


def html_links(path: Path) -> list[str]:
    parser = LinkParser()
    parser.feed(read_text(path))
    return parser.links


def is_external(href: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href)) and not href.startswith("file:")


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
        KNOWLEDGE_GRAPH / "index.html",
        HTML_LOGS / "index.html",
    ]
    pages.extend(sorted(PAPER_READING.glob("20*.html")))
    pages.extend(sorted(HTML_LOGS.glob("20*.html")))
    return [path for path in pages if path.exists()]


def all_generated_html_pages() -> list[Path]:
    pages = user_facing_html_pages()
    for directory in [PAPER_READING / "views", KNOWLEDGE_CARDS / "views", HTML_LOGS / "views"]:
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
        KNOWLEDGE_GRAPH / "index.html",
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
        add(checks, "易用性", "PASS", "用户入口没有裸 Markdown 直链", "主入口、今日页、知识卡、图谱和日志入口都指向可浏览页面。")


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


def check_review_queue(checks: list[Check], day: dt.date) -> None:
    rows = csv_rows(REVIEW_QUEUE)
    today = day.isoformat()
    due = [row for row in rows if row.get("next_review", "") <= today]
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
    check_review_queue(checks, day)
    check_backup(checks, day)
    check_git_backup(checks)
    check_context_budget(checks, day)
    check_hygiene(checks)
    return checks


def status_counts(checks: list[Check]) -> dict[str, int]:
    return {status: sum(1 for check in checks if check.status == status) for status in ["PASS", "WARN", "FAIL"]}


def markdown_report(day: dt.date, checks: list[Check]) -> str:
    counts = status_counts(checks)
    lines = [
        f"# Workflow Audit - {day.isoformat()}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
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
            "1. `make obsidian-graph`",
            "2. `make learning-dashboard`",
            "3. `make workflow-backup` when user-facing or evidence state changed",
            "4. `make workflow-audit`",
            "",
            "Use `make workflow-refresh` for the sequential no-race version of this closeout.",
            "",
        ]
    )
    return "\n".join(lines)


def html_report(day: dt.date, checks: list[Check]) -> str:
    counts = status_counts(checks)
    cards = "\n".join(
        f"""
        <article class="check {check.status.lower()}">
          <div class="status">{check.status}</div>
          <h2>{html.escape(check.title)}</h2>
          <p class="area">{html.escape(check.area)}</p>
          <p>{html.escape(check.detail)}</p>
        </article>
        """
        for check in checks
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ResearchWorkflow 体检</title>
  <style>
    :root {{ --ink:#182026; --muted:#65717d; --line:#d9e2ea; --paper:#fff; --bg:#f4f7fa; --pass:#16805d; --warn:#a15c07; --fail:#b4234b; --blue:#2463eb; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:radial-gradient(circle at top right, rgba(36,99,235,.11), transparent 28%), var(--bg); line-height:1.55; }}
    header {{ background:#102033; color:#f8fbff; }}
    .wrap {{ max-width:1180px; margin:0 auto; padding:26px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:0 0 8px; font-size:18px; }}
    p {{ margin:0 0 10px; }}
    a {{ color:var(--blue); text-decoration:none; }}
    .sub {{ color:rgba(248,251,255,.82); }}
    .nav {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:16px; }}
    .nav a {{ color:#f8fbff; border:1px solid rgba(255,255,255,.18); border-radius:999px; padding:7px 12px; background:rgba(255,255,255,.08); }}
    .metrics {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin:20px 0; }}
    .metric, .check {{ background:var(--paper); border:1px solid var(--line); border-radius:14px; box-shadow:0 10px 26px rgba(16,24,40,.05); }}
    .metric {{ padding:18px; }}
    .metric b {{ display:block; font-size:32px; line-height:1; }}
    .metric span {{ color:var(--muted); }}
    .checks {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .check {{ padding:16px; border-left:6px solid var(--line); }}
    .check.pass {{ border-left-color:var(--pass); }}
    .check.warn {{ border-left-color:var(--warn); }}
    .check.fail {{ border-left-color:var(--fail); }}
    .status {{ display:inline-flex; padding:2px 8px; border-radius:999px; background:#eef2f7; color:var(--muted); font-size:12px; font-weight:700; }}
    .pass .status {{ background:#eaf7f1; color:var(--pass); }}
    .warn .status {{ background:#fff5e6; color:var(--warn); }}
    .fail .status {{ background:#ffecef; color:var(--fail); }}
    .area {{ color:var(--muted); font-size:13px; }}
    footer {{ color:var(--muted); font-size:12px; }}
    @media (max-width: 860px) {{ .metrics, .checks {{ grid-template-columns:1fr; }} h1 {{ font-size:28px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>ResearchWorkflow 体检</h1>
      <p class="sub">Generated {dt.datetime.now().strftime("%Y-%m-%d %H:%M")} · PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}</p>
      <nav class="nav">
        <a href="study_dashboard.html">总览</a>
        <a href="paper_reading/today.html">今日精读</a>
        <a href="knowledge_graph/index.html">知识图谱</a>
        <a href="logs/index.html">学习日志</a>
      </nav>
    </div>
  </header>
  <main class="wrap">
    <section class="metrics">
      <div class="metric"><b>{counts['PASS']}</b><span>通过</span></div>
      <div class="metric"><b>{counts['WARN']}</b><span>提醒</span></div>
      <div class="metric"><b>{counts['FAIL']}</b><span>失败</span></div>
    </section>
    <section class="checks">{cards}</section>
  </main>
  <footer class="wrap">Run <code>make workflow-audit</code> to refresh this page.</footer>
</body>
</html>
"""


def write_reports(day: dt.date, checks: list[Check]) -> tuple[Path, Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = AUDIT_DIR / f"{day.isoformat()}-workflow-audit.md"
    md_path.write_text(markdown_report(day, checks) + "\n", encoding="utf-8")
    HEALTH_HTML.write_text(html_report(day, checks), encoding="utf-8")
    return md_path, HEALTH_HTML


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit ResearchWorkflow usability, links, graph, archive, and backup health.")
    parser.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on WARN as well as FAIL.")
    args = parser.parse_args()

    day = parse_date(args.date)
    checks = run_checks(day)
    md_path, html_path = write_reports(day, checks)
    counts = status_counts(checks)
    print(f"Wrote workflow audit: {md_path}")
    print(f"Wrote workflow health page: {html_path}")
    print(f"PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    if counts["FAIL"] or (args.strict and counts["WARN"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
