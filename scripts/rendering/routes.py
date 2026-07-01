from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from urllib.parse import quote, unquote

from rendering.paths import (
    CONCEPTS,
    DIRECTORY_VIEW_SOURCES,
    DIR_VIEWS,
    KNOWLEDGE_CARD_VIEWS,
    LEARNING_SESSIONS,
    LOG_VIEWS,
    MARKDOWN_VIEW_SOURCES,
    METHODS,
    PAPER_VIEWS,
    PROJECTS,
    ROOT,
    VAULT,
    esc,
    href,
    list_md,
    md_title,
    read_text,
)


def relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def path_is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


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


def directory_view_path(source: Path) -> Path:
    rel = relative_label(source)
    ascii_stem = re.sub(r"[^a-z0-9]+", "-", source.name.lower()).strip("-")
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:8]
    slug = f"{ascii_stem}-{digest}" if ascii_stem else f"directory-{digest}"
    return DIR_VIEWS / f"{slug}.html"


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


def local_child_path(source: Path | None, link: str) -> Path | None:
    raw = html.unescape(link).strip()
    base = raw.split("#", 1)[0].split("?", 1)[0]
    if not base or "://" in base or base.startswith(("mailto:", "obsidian:", "data:", "#")):
        return None
    if base.startswith("/"):
        candidate = Path(unquote(base)).resolve()
    else:
        parent = source.parent if source else ROOT
        candidate = (parent / unquote(base)).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def html_view_for_local_path(path: Path) -> Path:
    if path.suffix == ".md":
        if path.parent in {CONCEPTS, METHODS}:
            return card_view_path(path)
        if path.parent == LEARNING_SESSIONS:
            return log_view_path(path)
        return paper_markdown_view_path(path)
    if path.is_dir():
        readme = path / "README.md"
        if readme.exists():
            return html_view_for_local_path(readme)
        return directory_view_path(path)
    return path


def display_link_target(link: str, source: Path | None, output: Path | None) -> str:
    raw = html.unescape(link).strip()
    local_path = local_child_path(source, raw)
    if local_path and (local_path.exists() or local_path.suffix in {".md", ".html"}):
        target = html_view_for_local_path(local_path)
        rendered = href(target, output) if output else str(target)
        if "#" in raw and target.suffix == ".html":
            rendered += "#" + quote(raw.split("#", 1)[1], safe="=&%-_")
        return rendered
    return esc(raw)


def display_href(path: Path, output: Path) -> str:
    if path.suffix == ".md" and path.parent in {CONCEPTS, METHODS}:
        return href(card_view_path(path), output)
    if path.suffix == ".md" and path.parent == LEARNING_SESSIONS:
        return href(log_view_path(path), output)
    return href(path, output)


def local_markdown_source(page: Path, link: str) -> Path | None:
    source = local_child_path(page, link)
    if not source or source.suffix != ".md":
        return None
    return source


def is_standalone_markdown_view(source: Path) -> bool:
    if configured_paper_view(source):
        return source.suffix == ".md"
    return source.suffix == ".md" and source.parent not in {CONCEPTS, METHODS, LEARNING_SESSIONS}


def markdown_links_in_text(source: Path) -> list[Path]:
    text = read_text(source, limit=1_000_000)
    links: list[Path] = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = local_child_path(source, match.group(1))
        if target and target.suffix == ".md":
            links.append(target)
        elif target and target.is_dir() and (target / "README.md").exists():
            links.append(target / "README.md")
    for match in re.finditer(r'href=(["\'])([^"\']+?\.md(?:#[^"\']*)?)\1', text):
        target = local_child_path(source, html.unescape(match.group(2)))
        if target and target.suffix == ".md":
            links.append(target)
    return links


def directory_links_in_text(source: Path) -> list[Path]:
    text = read_text(source, limit=1_000_000)
    dirs: list[Path] = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = local_child_path(source, match.group(1))
        if target and target.is_dir() and not (target / "README.md").exists():
            dirs.append(target)
    return dirs


def seed_markdown_sources() -> list[Path]:
    seeds = [source for _, _, source, _ in MARKDOWN_VIEW_SOURCES]
    for project in sorted(PROJECTS.glob("*")):
        if not project.is_dir() or not (project / "project.yaml").exists():
            continue
        for relative in [
            "00_project_dashboard.md",
            "literature/reading_board.md",
            "literature/literature_review_workbench.md",
            "03_literature_synthesis.md",
            "literature/innovation_limitation_bank.md",
            "manuscript/evidence_gate_report.md",
        ]:
            source = project / relative
            if source.exists():
                seeds.append(source)
    seeds.extend(list_md(VAULT / "01_Literature"))
    seeds.extend(list_md(CONCEPTS))
    seeds.extend(list_md(METHODS))
    seeds.extend(list_md(LEARNING_SESSIONS))
    return seeds


def markdown_sources_from_paper_pages(paper_pages: list[Path]) -> list[Path]:
    sources: dict[Path, Path] = {}
    queue: list[Path] = []
    for source in seed_markdown_sources():
        resolved = source.resolve()
        if resolved not in sources:
            sources[resolved] = source
            queue.append(source)
    href_pattern = re.compile(r'href=(["\'])([^"\']+?\.md(?:#[^"\']*)?)\1')
    for page in paper_pages:
        text = read_text(page, limit=1_000_000)
        for match in href_pattern.finditer(text):
            source = local_markdown_source(page, html.unescape(match.group(2)))
            if source and source.resolve() not in sources:
                sources[source.resolve()] = source
                queue.append(source)
    while queue:
        current = queue.pop(0)
        if not current.exists():
            continue
        for target in markdown_links_in_text(current):
            resolved = target.resolve()
            if resolved in sources:
                continue
            sources[resolved] = target
            queue.append(target)
    standalone = [source for source in sources.values() if is_standalone_markdown_view(source)]
    return sorted(standalone, key=relative_label)


def directory_sources_from_markdown(markdown_sources: list[Path]) -> list[Path]:
    dirs: dict[Path, Path] = {}
    for directory in DIRECTORY_VIEW_SOURCES:
        dirs[directory.resolve()] = directory
    for source in markdown_sources:
        if source.exists():
            for directory in directory_links_in_text(source):
                dirs[directory.resolve()] = directory
    for source in [*list_md(CONCEPTS), *list_md(METHODS), *list_md(LEARNING_SESSIONS)]:
        for directory in directory_links_in_text(source):
            dirs[directory.resolve()] = directory
    return sorted(dirs.values(), key=relative_label)
