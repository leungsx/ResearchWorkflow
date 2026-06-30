from __future__ import annotations

import csv
from pathlib import Path

from rendering.paths import (
    ARTIFACT_MANIFEST,
    ACTION_QUEUE_HTML,
    ACTION_QUEUE_JSON,
    CONCEPTS,
    GRAPH_DIR,
    HTML_LOGS,
    KNOWLEDGE_CARDS,
    KNOWLEDGE_GRAPH,
    LEARNING_SESSIONS,
    METHODS,
    PAPER_READING,
    PROJECTS,
    REVIEW_QUEUE,
    REVIEW_STATE,
    REVIEW_TODAY,
    ROOT,
    SEARCH,
    SEARCH_INDEX_HTML,
    SEARCH_INDEX_JSON,
    WORKFLOW_AUDIT_JSON,
    WORKFLOW_HEALTH,
    WORKFLOW_STATE_HTML,
    WORKFLOW_STATE_JSON,
    html_title,
    list_md,
    md_title,
    paper_pages,
)
from rendering.routes import (
    card_view_path,
    directory_sources_from_markdown,
    directory_view_path,
    log_view_path,
    markdown_sources_from_paper_pages,
    paper_markdown_view_path,
    paper_markdown_view_title,
    path_is_under,
    relative_label,
)


def source_type_for(path: Path) -> str:
    if path.is_dir():
        return "directory"
    if path.suffix == ".md":
        return "markdown"
    if path.suffix == ".html":
        return "html"
    if path.suffix == ".csv":
        return "csv"
    if path.suffix in {".yaml", ".yml"}:
        return "yaml"
    if path.suffix == ".json":
        return "json"
    return path.suffix.lstrip(".") or "file"


def layer_for_source(path: Path) -> str:
    if path.suffix == ".html" and path.parent == ROOT:
        return "Presentation"
    if path_is_under(path, PAPER_READING) or path_is_under(path, KNOWLEDGE_CARDS) or path_is_under(path, KNOWLEDGE_GRAPH) or path_is_under(path, SEARCH) or path_is_under(path, HTML_LOGS):
        if path.suffix == ".html":
            return "Presentation"
    if path_is_under(path, ROOT / "library"):
        return "Source"
    if "readers" in path.parts:
        return "Source"
    if path_is_under(path, ROOT / "vault") or path_is_under(path, ROOT / "projects"):
        return "Knowledge"
    if path_is_under(path, ROOT / "scripts") or path.name == "Makefile":
        return "Processing"
    return "Orchestration/QA"


def artifact_title(path: Path) -> str:
    if path.is_dir():
        return path.name
    if path.suffix == ".md":
        return md_title(path)
    if path.suffix == ".html":
        return html_title(path)
    return path.name


def collect_directory_tree(seeds: list[Path]) -> list[Path]:
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


def artifact_manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(source: Path, display: Path, display_type: str, title: str | None = None, generated_by: str = "make learning-dashboard") -> None:
        key = (relative_label(source), relative_label(display), display_type)
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "source_path": relative_label(source),
                "source_type": source_type_for(source),
                "display_path": relative_label(display),
                "display_type": display_type,
                "title": title or artifact_title(source),
                "layer": layer_for_source(source),
                "generated_by": generated_by,
            }
        )

    for source, display_type, title in [
        (ROOT / "study_dashboard.html", "dashboard", "ResearchWorkflow 学习仪表盘"),
        (PAPER_READING / "today.html", "paper_today_entry", "今日精读入口"),
        (PAPER_READING / "index.html", "paper_index", "论文精读归档"),
        (KNOWLEDGE_CARDS / "index.html", "knowledge_cards_index", "知识卡入口"),
        (REVIEW_TODAY, "review_today", "今日复习入口"),
        (KNOWLEDGE_GRAPH / "index.html", "knowledge_graph", "知识图谱入口"),
        (SEARCH_INDEX_HTML, "search", "全局搜索入口"),
        (HTML_LOGS / "index.html", "logs_index", "学习日志入口"),
        (WORKFLOW_STATE_HTML, "workflow_state", "工作流总状态"),
        (ACTION_QUEUE_HTML, "action_queue", "行动队列"),
    ]:
        if source.exists():
            add(source, source, display_type, title)

    pages = paper_pages()
    markdown_sources = markdown_sources_from_paper_pages(pages)

    for page in pages:
        add(page, page, "paper_page", html_title(page))

    for source in markdown_sources:
        add(source, paper_markdown_view_path(source), "markdown_view", paper_markdown_view_title(source))

    for source in list_md(CONCEPTS):
        add(source, card_view_path(source), "concept_card_view", md_title(source))

    for source in list_md(METHODS):
        add(source, card_view_path(source), "method_card_view", md_title(source))

    for source in list_md(LEARNING_SESSIONS):
        add(source, log_view_path(source), "log_view", md_title(source))

    directory_sources = collect_directory_tree(directory_sources_from_markdown(markdown_sources))
    for directory in directory_sources:
        for source in sorted(directory.glob("*.md"), key=relative_label):
            add(source, paper_markdown_view_path(source), "markdown_view", paper_markdown_view_title(source))

    for source in directory_sources:
        add(source, directory_view_path(source), "directory_view", source.name)

    for project in sorted([path for path in PROJECTS.iterdir() if path.is_dir() and (path / "project.yaml").exists()]):
        dashboard = project / "00_project_dashboard.md"
        add(project / "project_state.json", paper_markdown_view_path(dashboard), "project_state", f"{project.name} project state")

    for source, title in [
        (GRAPH_DIR / "obsidian_nodes.csv", "Obsidian graph nodes"),
        (GRAPH_DIR / "obsidian_edges.csv", "Obsidian graph edges"),
        (GRAPH_DIR / "knowledge_index.csv", "Knowledge card index"),
        (ARTIFACT_MANIFEST, "Artifact manifest"),
    ]:
        add(source, KNOWLEDGE_GRAPH / "index.html", "graph_source_data", title, "make obsidian-graph && make learning-dashboard")

    add(REVIEW_QUEUE, REVIEW_TODAY, "review_queue", "Review queue")
    add(REVIEW_STATE, REVIEW_TODAY, "review_state", "Review state")
    add(SEARCH_INDEX_JSON, SEARCH_INDEX_HTML, "search_index", "Search index")
    add(WORKFLOW_STATE_JSON, WORKFLOW_STATE_HTML, "workflow_state_data", "Workflow state")
    add(ACTION_QUEUE_JSON, ACTION_QUEUE_HTML, "action_queue_data", "Action queue")
    add(WORKFLOW_AUDIT_JSON, WORKFLOW_HEALTH, "workflow_audit_data", "Workflow audit report")

    rows.sort(key=lambda row: (row["display_type"], row["source_path"], row["display_path"]))
    return rows


def build_artifact_manifest() -> None:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = ["source_path", "source_type", "display_path", "display_type", "title", "layer", "generated_by"]
    rows = artifact_manifest_rows()
    with ARTIFACT_MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
