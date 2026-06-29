#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELATIONS = ROOT / "library" / "relations.csv"
DEFAULT_OUTPUT = ROOT / "library" / "gephi"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export relation CSV to Gephi nodes and edges.")
    parser.add_argument("--relations", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.relations.exists():
        args.relations.parent.mkdir(parents=True, exist_ok=True)
        args.relations.write_text("source,target,relation,weight,evidence\n", encoding="utf-8")
        print(f"Created relation template: {args.relations}")
        return 0

    rows = list(csv.DictReader(args.relations.open(encoding="utf-8")))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    nodes = {}
    edges = []
    for idx, row in enumerate(rows, start=1):
        source = (row.get("source") or "").strip()
        target = (row.get("target") or "").strip()
        if not source or not target:
            continue
        nodes[source] = {"Id": source, "Label": source, "Type": "item"}
        nodes[target] = {"Id": target, "Label": target, "Type": "item"}
        edges.append(
            {
                "Source": source,
                "Target": target,
                "Type": "Undirected",
                "Weight": row.get("weight") or "1",
                "Label": row.get("relation") or f"edge_{idx}",
                "Relation": row.get("relation") or "",
                "Evidence": row.get("evidence") or "",
            }
        )

    nodes_path = args.output_dir / "nodes.csv"
    edges_path = args.output_dir / "edges.csv"
    with nodes_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Id", "Label", "Type"])
        writer.writeheader()
        writer.writerows(nodes.values())
    with edges_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Source", "Target", "Type", "Weight", "Label", "Relation", "Evidence"])
        writer.writeheader()
        writer.writerows(edges)

    print(f"Wrote {len(nodes)} nodes to {nodes_path}")
    print(f"Wrote {len(edges)} edges to {edges_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

