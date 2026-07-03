from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rendering.paths import (
    ARCHIVE_POLICY_HTML,
    COLLABORATION_HTML,
    KNOWLEDGE_CARDS,
    KNOWLEDGE_GRAPH,
    PAPER_READING,
    PAPER_VIEWS,
    PROJECTS,
    REVIEW_TODAY,
    ROOT,
    SEARCH_INDEX_HTML,
    WORKFLOW_HEALTH,
    WORKFLOW_STATE_HTML,
    esc,
    href,
)
from workflow_config import active_project_slug


ASSETS = ROOT / "assets"
APP_CSS = ASSETS / "app.css"
APP_JS = ASSETS / "app.js"


@dataclass(frozen=True)
class NavItem:
    label: str
    target: Path
    aliases: tuple[str, ...] = ()


def active_project_path(*parts: str) -> Path:
    return PROJECTS / active_project_slug() / Path(*parts)


def existing(target: Path) -> bool:
    return target.exists()


def global_nav_items() -> list[NavItem]:
    writing = active_project_path("manuscript", "writing_panel.html")
    evidence = active_project_path("evidence", "page_verification_queue.html")
    if not evidence.exists():
        evidence = active_project_path("literature", "evidence_locator_table.html")
    return [
        NavItem("总览", ROOT / "study_dashboard.html", ("总览首页", "学习仪表盘")),
        NavItem("今日任务", ROOT / "action_queue.html", ("行动队列", "任务总览")),
        NavItem("阅读", PAPER_READING / "today.html", ("今日精读", "论文归档", "知识卡", "PDF分拣")),
        NavItem("写作", writing if writing.exists() else WORKFLOW_STATE_HTML, ("论文写作", "论文写作面板")),
        NavItem("证据", evidence if evidence.exists() else WORKFLOW_STATE_HTML, ("证据定位", "页码核验", "主张证据表")),
        NavItem("系统", WORKFLOW_STATE_HTML, ("工作流状态", "总状态", "工作流体检", "项目协作", "归档策略", "学习日志")),
    ]


def module_for(current: str) -> str:
    mapping = {
        "总览": "总览",
        "总览首页": "总览",
        "学习仪表盘": "总览",
        "搜索": "总览",
        "全局搜索": "总览",
        "知识图谱": "总览",
        "今日任务": "今日任务",
        "行动队列": "今日任务",
        "任务总览": "今日任务",
        "复习": "今日任务",
        "今日复习": "今日任务",
        "今日精读": "阅读",
        "论文归档": "阅读",
        "知识卡": "阅读",
        "PDF分拣": "阅读",
        "Reader": "阅读",
        "论文写作": "写作",
        "论文写作面板": "写作",
        "证据定位": "证据",
        "页码核验": "证据",
        "主张证据表": "证据",
        "工作流状态": "系统",
        "总状态": "系统",
        "工作流体检": "系统",
        "项目协作": "系统",
        "归档策略": "系统",
        "自动归档策略": "系统",
        "学习日志": "系统",
        "Vault 首页": "系统",
    }
    return mapping.get(current, "总览")


def subnav_items(module: str) -> list[NavItem]:
    incoming = active_project_path("literature", "incoming_pdf_triage.html")
    evidence_locator = active_project_path("literature", "evidence_locator_table.html")
    verification = active_project_path("evidence", "page_verification_queue.html")
    writing = active_project_path("manuscript", "writing_panel.html")
    vault_home = PAPER_VIEWS / "vault-home.html"
    items: dict[str, list[NavItem]] = {
        "总览": [
            NavItem("总览首页", ROOT / "study_dashboard.html", ("总览",)),
            NavItem("今日精读", PAPER_READING / "today.html"),
            NavItem("今日复习", REVIEW_TODAY, ("复习",)),
            NavItem("搜索", SEARCH_INDEX_HTML, ("全局搜索",)),
            NavItem("知识图谱", KNOWLEDGE_GRAPH / "index.html"),
            NavItem("Vault 首页", vault_home),
        ],
        "今日任务": [
            NavItem("任务总览", ROOT / "action_queue.html", ("今日任务", "行动队列")),
            NavItem("今日复习", REVIEW_TODAY, ("复习",)),
            NavItem("今日精读", PAPER_READING / "today.html"),
            NavItem("写作推进", writing, ("论文写作", "论文写作面板")),
        ],
        "阅读": [
            NavItem("今日精读", PAPER_READING / "today.html"),
            NavItem("论文归档", PAPER_READING / "index.html"),
            NavItem("PDF分拣", incoming),
            NavItem("知识卡", KNOWLEDGE_CARDS / "index.html"),
        ],
        "写作": [
            NavItem("论文写作面板", writing, ("论文写作",)),
            NavItem("页码核验", verification),
            NavItem("证据定位", evidence_locator),
        ],
        "证据": [
            NavItem("证据定位", evidence_locator),
            NavItem("页码核验", verification),
            NavItem("论文写作面板", writing, ("写作核验", "论文写作")),
        ],
        "系统": [
            NavItem("工作流状态", WORKFLOW_STATE_HTML, ("总状态",)),
            NavItem("工作流体检", WORKFLOW_HEALTH),
            NavItem("归档策略", ARCHIVE_POLICY_HTML, ("自动归档策略",)),
            NavItem("项目协作", COLLABORATION_HTML, ("项目协作层",)),
            NavItem("学习日志", ROOT / "logs" / "index.html"),
        ],
    }
    return [item for item in items.get(module, []) if existing(item.target)]


def is_active(item: NavItem, current: str, module: str | None = None) -> bool:
    return item.label == current or current in item.aliases or (module is not None and item.label == module)


def render_nav(items: list[NavItem], output: Path, current: str, *, class_name: str, label: str, module: str | None = None) -> str:
    links: list[str] = []
    for item in items:
        current_attr = ' aria-current="page"' if is_active(item, current, module) else ""
        links.append(f'<a href="{href(item.target, output)}"{current_attr}>{esc(item.label)}</a>')
    return f'<nav class="nav {class_name}" aria-label="{esc(label)}">' + "\n".join(links) + "</nav>"


def page_needs_app_js(body: str) -> bool:
    return "data-copy=" in body or "data-mode-button" in body or "data-mode=" in body


def render_shell(
    *,
    title: str,
    subtitle: str,
    current: str,
    body: str,
    output: Path,
    module: str | None = None,
    meta: str | None = None,
    primary_action: str = "",
    footer: str = "Generated by ResearchWorkflow.",
) -> str:
    current_module = module or module_for(current)
    body_html = body.strip()
    css_href = href(APP_CSS, output)
    script = f'\n  <script src="{href(APP_JS, output)}" defer></script>' if page_needs_app_js(body) else ""
    meta_html = f'<p class="page-meta">{esc(meta)}</p>' if meta else f'<p class="page-meta">当前项目：{esc(active_project_slug())}</p>'
    action_html = f'<div class="page-primary-action">{primary_action}</div>' if primary_action else '<div class="page-primary-action" hidden></div>'
    global_nav = render_nav(global_nav_items(), output, current, class_name="global-nav", label="一级导航", module=current_module)
    subnav = render_nav(subnav_items(current_module), output, current, class_name="subnav", label=f"{current_module}子导航")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{css_href}">
{script}
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <header class="site-header">
    <div class="wrap">
      <p class="page-kicker">ResearchWorkflow / {esc(current_module)}</p>
      <div class="page-heading">
        <div>
          <h1>{esc(title)}</h1>
          <p class="sub">{esc(subtitle)}</p>
          {meta_html}
        </div>
        {action_html}
      </div>
      {global_nav}
      {subnav}
    </div>
  </header>
  <main class="wrap" id="main-content">
{body_html}
  </main>
  <footer class="wrap">{esc(footer)}</footer>
</body>
</html>
"""
