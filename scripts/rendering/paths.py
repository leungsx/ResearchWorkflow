from __future__ import annotations

import csv
import html
import os
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "vault"
PROJECTS = ROOT / "projects"
PAPER_READING = ROOT / "paper_reading"
HTML_LOGS = ROOT / "logs"
KNOWLEDGE_CARDS = ROOT / "knowledge_cards"
KNOWLEDGE_GRAPH = ROOT / "knowledge_graph"
SEARCH = ROOT / "search"
PAPER_VIEWS = PAPER_READING / "views"
KNOWLEDGE_CARD_VIEWS = KNOWLEDGE_CARDS / "views"
LOG_VIEWS = HTML_LOGS / "views"
DIR_VIEWS = PAPER_VIEWS / "directories"
WORKFLOW_HEALTH = ROOT / "workflow_health.html"
WORKFLOW_STATE_HTML = ROOT / "workflow_state.html"
ACTION_QUEUE_HTML = ROOT / "action_queue.html"
BACKUP_INDEX = ROOT / "backups" / "index.html"
PAPER_RESERVED = {"index.html", "today.html"}

CONCEPTS = VAULT / "02_Concepts"
METHODS = VAULT / "03_Methods"
LEARNING_SESSIONS = VAULT / "12_Learning_Log" / "sessions"
GRAPH_DIR = VAULT / "13_Knowledge_Graph"
REVIEW_QUEUE = VAULT / "14_Review_Queue" / "review_queue.csv"
REVIEW_STATE = VAULT / "14_Review_Queue" / "review_state.json"
ARTIFACT_MANIFEST = GRAPH_DIR / "artifact_manifest.csv"
REVIEW_TODAY = KNOWLEDGE_CARDS / "review_today.html"
SEARCH_INDEX_JSON = GRAPH_DIR / "search_index.json"
SEARCH_INDEX_HTML = SEARCH / "index.html"
WORKFLOW_STATE_JSON = GRAPH_DIR / "workflow_state.json"
ACTION_QUEUE_JSON = GRAPH_DIR / "action_queue.json"
WORKFLOW_AUDIT_JSON = GRAPH_DIR / "workflow_audit_report.json"

MARKDOWN_VIEW_SOURCES = [
    (
        "vault-home",
        "Vault 首页",
        VAULT / "Home.md",
        "Obsidian Home 的浏览器友好镜像页。",
    ),
    (
        "workflow_layered_architecture",
        "分层架构契约",
        ROOT / "docs" / "WORKFLOW_LAYERED_ARCHITECTURE.md",
        "ResearchWorkflow 的源资产、加工层、知识层、展示层和质检层边界。",
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
    (
        "2026-06-20-library-short-video",
        "2026-06-20 CNKI 每日推荐",
        VAULT / "15_CNKI_Frontier" / "daily_recommendations" / "2026-06-20-library_short_video.md",
        "图书馆短视频项目上一轮 CNKI 推荐报告浏览版。",
    ),
]

DIRECTORY_VIEW_SOURCES = [
    ROOT / "projects" / "library_short_video" / "literature" / "context_packs",
    VAULT / "15_CNKI_Frontier" / "paper_briefs",
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
