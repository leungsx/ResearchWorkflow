#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
OUTPUT = VAULT / "13_Knowledge_Graph"
LITERATURE_MATRIX = ROOT / "library" / "literature_matrix.csv"
EXCLUDED_TOP_LEVEL_DIRS = {"99_Templates"}
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
CITEKEY_RE = re.compile(r"^cnki_\d{4}_[A-Za-z0-9]+$")


def note_id(path: Path) -> str:
    return path.stem


def note_type(path: Path) -> str:
    parts = path.relative_to(VAULT).parts
    if not parts:
        return "note"
    if len(parts) == 1:
        return "home" if path.name == "Home.md" else "note"
    mapping = {
        "01_Literature": "literature",
        "02_Concepts": "concept",
        "03_Methods": "method",
        "04_Projects": "project",
        "11_Idea_Lab": "idea",
        "12_Learning_Log": "learning",
    }
    return mapping.get(parts[0], parts[0])


def clean_scalar(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value.strip()


def frontmatter_value(text: str, key: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        if name.strip() == key:
            return clean_scalar(value)
    return ""


def first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def plain_field(text: str, key: str) -> str:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return clean_scalar(line[len(prefix) :])
    return ""


def load_literature_titles(path: Path = LITERATURE_MATRIX) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return {
            row["citekey"].strip(): row["title"].strip()
            for row in rows
            if row.get("citekey") and row.get("title")
        }


def load_project_titles(vault: Path) -> dict[str, str]:
    project_dir = vault / "04_Projects"
    if not project_dir.exists():
        return {}
    labels: dict[str, str] = {}
    for path in project_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        slug = frontmatter_value(text, "slug") or path.stem
        title = frontmatter_value(text, "title") or first_heading(text)
        if slug and title:
            labels[slug] = title
    return labels


def clean_display_label(label: str, project_titles: dict[str, str]) -> str:
    label = label.strip()
    phrase_replacements = {
        "Brainstorm Session -": "头脑风暴 -",
        "CNKI Frontier": "CNKI 前沿雷达",
        "CNKI Intake Report -": "CNKI 导入报告 -",
        "Compact Daily Summary -": "每日摘要 -",
        "Context Pack -": "上下文包 -",
        "Daily Codex Log -": "每日 Codex 日志 -",
        "File Sweep -": "文件整理记录 -",
        "Workflow Audit -": "工作流审计 -",
        "Weekly Codex Review -": "每周 Codex 复盘 -",
    }
    exact_replacements = {
        "11 Idea Lab/README": "想法实验室 README",
        "Idea Lab": "想法实验室",
        "Inbox": "收件箱",
        "Starter Research Project": "研究项目模板",
        "User Model": "用户模型",
    }
    if label in exact_replacements:
        label = exact_replacements[label]
    for old, new in phrase_replacements.items():
        label = label.replace(old, new)
    for slug, title in project_titles.items():
        label = label.replace(slug, title)
    return label


def humanize_identifier(identifier: str) -> str:
    if CITEKEY_RE.match(identifier):
        return identifier
    if re.search(r"[\u4e00-\u9fff]", identifier):
        return identifier
    label = re.sub(r"[-_][0-9a-f]{8}$", "", identifier)
    label = label.replace("_", " ").replace("-", " ")
    replacements = {
        "library short video": "图书馆短视频",
        "sicas paper": "SICAS 论文精读",
        "aarrr paper": "AARRR 论文精读",
        "evening close": "晚间闭环",
        "digital reading promotion paper": "数字阅读推广论文精读",
    }
    for old, new in replacements.items():
        label = label.replace(old, new)
    return " ".join(label.split()) or identifier


def clean_heading_label(label: str, text: str, path: Path) -> str:
    label = label.removeprefix("Learning Session - ").strip()
    if "12_Learning_Log" in path.parts and re.match(r"\d{4}-\d{2}-\d{2} Evening Close$", label):
        return plain_field(text, "Topic") or label
    return label


def note_label(path: Path, text: str, literature_titles: dict[str, str], project_titles: dict[str, str]) -> str:
    identifier = note_id(path)
    if identifier in literature_titles:
        return clean_display_label(literature_titles[identifier], project_titles)
    title = frontmatter_value(text, "title")
    if title:
        return clean_display_label(title, project_titles)
    heading = first_heading(text)
    if heading:
        return clean_display_label(clean_heading_label(heading, text, path), project_titles)
    return clean_display_label(humanize_identifier(identifier), project_titles)


def link_label(target: str, alias: str, literature_titles: dict[str, str], project_titles: dict[str, str]) -> str:
    if target in literature_titles:
        return clean_display_label(literature_titles[target], project_titles)
    if alias.strip():
        return clean_display_label(alias, project_titles)
    return clean_display_label(humanize_identifier(target), project_titles)


def orphan_label_is_placeholder(node: dict[str, str], literature_titles: dict[str, str], project_titles: dict[str, str]) -> bool:
    expected = link_label(node["Id"], "", literature_titles, project_titles)
    return node["Label"] == expected or node["Label"] == node["Id"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Obsidian wiki links as Gephi-ready nodes and edges.")
    parser.add_argument("--vault", type=Path, default=VAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()

    literature_titles = load_literature_titles()
    project_titles = load_project_titles(args.vault)
    nodes: dict[str, dict[str, str]] = {}
    edge_weights: Counter[tuple[str, str, str]] = Counter()
    for path in sorted(args.vault.rglob("*.md")):
        relative_parts = path.relative_to(args.vault).parts
        if ".obsidian" in path.parts or (relative_parts and relative_parts[0] in EXCLUDED_TOP_LEVEL_DIRS):
            continue
        source = note_id(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        nodes[source] = {"Id": source, "Label": note_label(path, text, literature_titles, project_titles), "Type": note_type(path)}
        for target, alias in LINK_RE.findall(text):
            target = target.strip()
            if not target:
                continue
            if target not in nodes:
                nodes[target] = {
                    "Id": target,
                    "Label": link_label(target, alias, literature_titles, project_titles),
                    "Type": "linked",
                }
            elif (
                alias.strip()
                and nodes[target]["Type"] == "linked"
                and orphan_label_is_placeholder(nodes[target], literature_titles, project_titles)
            ):
                nodes[target]["Label"] = clean_display_label(alias, project_titles)
            edge_weights[(source, target, "obsidian_link")] += 1

    edges = [
        {
            "Source": source,
            "Target": target,
            "Type": "Directed",
            "Weight": str(weight),
            "Label": label,
        }
        for (source, target, label), weight in sorted(edge_weights.items())
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = args.output_dir / "obsidian_nodes.csv"
    edges_path = args.output_dir / "obsidian_edges.csv"
    with nodes_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Id", "Label", "Type"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(nodes.values())
    with edges_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Source", "Target", "Type", "Weight", "Label"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(edges)

    print(f"Wrote {len(nodes)} nodes to {nodes_path}")
    print(f"Wrote {len(edges)} edges to {edges_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
