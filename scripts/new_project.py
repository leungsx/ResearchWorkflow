#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
TEMPLATE = PROJECTS / "_template"
VAULT_PROJECTS = ROOT / "vault" / "04_Projects"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Project slug cannot be empty.")
    return value


def replace_placeholders(path: Path, replacements: dict[str, str]) -> None:
    text_suffixes = {".md", ".py", ".R", ".m", ".bib", ".txt", ".yaml", ".yml"}
    for item in path.rglob("*"):
        if not item.is_file() or item.suffix not in text_suffixes:
            continue
        text = item.read_text(encoding="utf-8")
        for key, value in replacements.items():
            text = text.replace(key, value)
        item.write_text(text, encoding="utf-8")


def create_project(slug: str, title: str) -> Path:
    slug = slugify(slug)
    dest = PROJECTS / slug
    if dest.exists():
        raise FileExistsError(f"Project already exists: {dest}")
    shutil.copytree(TEMPLATE, dest)

    replacements = {
        "{{PROJECT_SLUG}}": slug,
        "{{PROJECT_TITLE}}": title,
    }
    replace_placeholders(dest, replacements)

    metadata = dest / "project.yaml"
    metadata.write_text(
        "\n".join(
            [
                f"slug: {slug}",
                f"title: {title}",
                f"created_at: {dt.datetime.now().isoformat(timespec='seconds')}",
                "status: draft",
                "",
            ]
        ),
        encoding="utf-8",
    )

    VAULT_PROJECTS.mkdir(parents=True, exist_ok=True)
    note = VAULT_PROJECTS / f"{slug}.md"
    note.write_text(
        "\n".join(
            [
                "---",
                "type: project",
                f"slug: {slug}",
                f"title: \"{title}\"",
                "status: draft",
                "---",
                "",
                f"# {title}",
                "",
                f"Project folder: `{dest}`",
                f"Dashboard: `{dest / '00_project_dashboard.md'}`",
                "",
                "## Current Question",
                "",
                "## Key Literature",
                "",
                "## Data / Experiments",
                "",
                "## Manuscript",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new research project.")
    parser.add_argument("slug", help="ASCII project id, e.g. ai_qa_2026")
    parser.add_argument("title", nargs="?", help="Human-readable project title")
    args = parser.parse_args()

    title = args.title or args.slug.replace("_", " ").replace("-", " ").title()
    dest = create_project(args.slug, title)
    print(f"Created project: {dest}")
    print(f"Open Obsidian note: {VAULT_PROJECTS / (slugify(args.slug) + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
