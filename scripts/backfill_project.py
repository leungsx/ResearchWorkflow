#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
TEMPLATE = PROJECTS / "_template"

TEXT_SUFFIXES = {
    ".bib",
    ".csv",
    ".m",
    ".md",
    ".py",
    ".R",
    ".txt",
    ".yaml",
    ".yml",
}


def read_project_metadata(project: Path) -> dict[str, str]:
    metadata = project / "project.yaml"
    values: dict[str, str] = {}
    if not metadata.exists():
        return values
    for raw_line in metadata.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def replacements_for(project: Path) -> dict[str, str]:
    meta = read_project_metadata(project)
    slug = meta.get("slug") or project.name
    title = meta.get("title") or project.name.replace("_", " ").replace("-", " ").title()
    return {
        "{{PROJECT_SLUG}}": slug,
        "{{PROJECT_TITLE}}": title,
    }


def template_files() -> list[Path]:
    files = []
    for path in sorted(TEMPLATE.rglob("*")):
        if path.is_file() and path.name != ".DS_Store":
            files.append(path)
    return files


def write_backfilled_file(source: Path, dest: Path, replacements: dict[str, str]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix in TEXT_SUFFIXES:
        text = source.read_text(encoding="utf-8", errors="ignore")
        for key, value in replacements.items():
            text = text.replace(key, value)
        dest.write_text(text, encoding="utf-8")
    else:
        shutil.copy2(source, dest)


def backfill_project(project: Path, apply: bool) -> tuple[list[str], list[str]]:
    if not project.exists():
        raise FileNotFoundError(project)
    if project.name == "_template":
        raise ValueError("Do not backfill the template project.")

    replacements = replacements_for(project)
    missing: list[str] = []
    existing: list[str] = []

    for source in template_files():
        rel = source.relative_to(TEMPLATE)
        dest = project / rel
        rel_text = rel.as_posix()
        if dest.exists():
            existing.append(rel_text)
            continue
        missing.append(rel_text)
        if apply:
            write_backfilled_file(source, dest, replacements)

    return missing, existing


def iter_projects() -> list[Path]:
    return [
        path
        for path in sorted(PROJECTS.iterdir())
        if path.is_dir() and not path.name.startswith(".") and path.name != "_template"
    ]


def print_project_report(project: Path, missing: list[str], existing: list[str], apply: bool) -> None:
    print(f"\n## {project.name}")
    print(f"- Existing template files: {len(existing)}")
    print(f"- Missing template files: {len(missing)}")
    if not missing:
        print("- Action: already up to date")
        return
    print(f"- Action: {'copied' if apply else 'dry-run only'}")
    for rel in missing:
        prefix = "COPIED" if apply else "WOULD COPY"
        print(f"- {prefix}: {rel}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill existing projects with files added to projects/_template without overwriting user files."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="Project slug under projects/")
    group.add_argument("--all", action="store_true", help="Backfill all non-template projects")
    parser.add_argument("--apply", action="store_true", help="Actually copy missing files. Default is dry-run.")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(TEMPLATE)

    projects = iter_projects() if args.all else [PROJECTS / args.project]
    print("# Project Backfill Report")
    print(f"\nMode: {'apply' if args.apply else 'dry-run'}")

    total_missing = 0
    for project in projects:
        missing, existing = backfill_project(project, apply=args.apply)
        total_missing += len(missing)
        print_project_report(project, missing, existing, apply=args.apply)

    print("\n## Summary")
    print(f"- Projects checked: {len(projects)}")
    print(f"- Missing files found: {total_missing}")
    if not args.apply and total_missing:
        print("- Re-run with `--apply` to copy the missing files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
