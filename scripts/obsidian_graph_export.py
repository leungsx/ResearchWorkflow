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
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")


def note_id(path: Path) -> str:
    return path.stem


def note_type(path: Path) -> str:
    parts = path.relative_to(VAULT).parts
    if not parts:
        return "note"
    mapping = {
        "01_Literature": "literature",
        "02_Concepts": "concept",
        "03_Methods": "method",
        "04_Projects": "project",
        "11_Idea_Lab": "idea",
        "12_Learning_Log": "learning",
    }
    return mapping.get(parts[0], parts[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Obsidian wiki links as Gephi-ready nodes and edges.")
    parser.add_argument("--vault", type=Path, default=VAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()

    nodes: dict[str, dict[str, str]] = {}
    edge_weights: Counter[tuple[str, str, str]] = Counter()
    for path in sorted(args.vault.rglob("*.md")):
        if ".obsidian" in path.parts:
            continue
        source = note_id(path)
        nodes[source] = {"Id": source, "Label": source, "Type": note_type(path)}
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in LINK_RE.findall(text):
            target = target.strip()
            if not target:
                continue
            nodes.setdefault(target, {"Id": target, "Label": target, "Type": "linked"})
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
