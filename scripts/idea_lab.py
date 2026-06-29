#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
IDEA_LAB = VAULT / "11_Idea_Lab"
SESSIONS = IDEA_LAB / "sessions"
CARDS = IDEA_LAB / "idea_cards"
FRONTIER = IDEA_LAB / "frontier_scans"
INCUBATOR = IDEA_LAB / "incubator"
PROMOTED = IDEA_LAB / "promoted_projects"
INDEX = IDEA_LAB / "idea_index.csv"


INDEX_FIELDS = [
    "idea_id",
    "title",
    "status",
    "created_at",
    "source_session",
    "domain",
    "frontier_needed",
    "finer_avg",
    "next_action",
    "note_path",
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "idea"


def ensure_index() -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        with INDEX.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
            writer.writeheader()


def append_index(row: dict[str, str]) -> None:
    ensure_index()
    with INDEX.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writerow(row)


def start_session(args: argparse.Namespace) -> int:
    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    stamp = dt.datetime.now().strftime("%H%M%S")
    slug = slugify(args.topic)
    path = SESSIONS / f"{day.isoformat()}-{stamp}-{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# Brainstorm Session - {args.topic}

Date: {day.isoformat()}
Mode: {args.mode}
Status: open

## Starting Prompt

{args.topic}

## Context Inputs

- Current context: `/Users/leung/ResearchWorkflow/codex/state/current_context.md`
- User model: `/Users/leung/ResearchWorkflow/codex/state/user_model.md`
- Literature matrix: `/Users/leung/ResearchWorkflow/library/literature_matrix.csv`
- Open loops: `/Users/leung/ResearchWorkflow/codex/state/open_loops.md`

## Socratic Questions

1.
2.
3.

## Raw Ideas

## Knowledge Recombination

## Frontier Signals To Check

## Candidate Research Questions

## FINER Notes

## Decisions

## Next Actions

"""
    path.write_text(content, encoding="utf-8")
    print(f"Created brainstorm session: {path}")
    return 0


def add_idea(args: argparse.Namespace) -> int:
    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    slug = slugify(args.title)
    idea_id = f"{day.strftime('%Y%m%d')}-{slug}"
    path = CARDS / f"{idea_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not args.overwrite:
        raise FileExistsError(f"Idea card already exists: {path}")
    content = f"""---
type: idea
idea_id: {idea_id}
title: "{args.title}"
status: seed
created_at: {dt.datetime.now().isoformat(timespec='seconds')}
domain: "{args.domain or ''}"
frontier_needed: {str(args.frontier_needed).lower()}
---

# {args.title}

## One-Sentence Idea

{args.summary or ''}

## Why It Might Matter

## What Existing Knowledge It Connects

## What Frontier Needs Checking

## Possible Research Questions

## Possible Data / Method

## FINER Self-Check

| Criterion | Score | Note |
|---|---:|---|
| Feasible |  |  |
| Interesting |  |  |
| Novel |  |  |
| Ethical |  |  |
| Relevant |  |  |

## Risks / Weaknesses

## Next Action

"""
    path.write_text(content, encoding="utf-8")
    append_index(
        {
            "idea_id": idea_id,
            "title": args.title,
            "status": "seed",
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "source_session": args.session or "",
            "domain": args.domain or "",
            "frontier_needed": "yes" if args.frontier_needed else "no",
            "finer_avg": "",
            "next_action": args.next_action or "Discuss with Codex in Socratic mode",
            "note_path": str(path),
        }
    )
    print(f"Created idea card: {path}")
    print(f"Updated index: {INDEX}")
    return 0


def status(_: argparse.Namespace) -> int:
    ensure_index()
    sessions = sorted(SESSIONS.glob("*.md"))
    cards = sorted(CARDS.glob("*.md"))
    scans = sorted(FRONTIER.glob("*.md"))
    print("# Idea Lab Status\n")
    print(f"- Brainstorm sessions: {len(sessions)}")
    print(f"- Idea cards: {len(cards)}")
    print(f"- Frontier scans: {len(scans)}")
    print(f"- Idea index: {INDEX}")
    if cards:
        print("\n## Recent Idea Cards")
        for card in cards[-10:]:
            print(f"- {card.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain the ResearchWorkflow Idea Lab.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Create a new brainstorm session note.")
    p_start.add_argument("--topic", required=True)
    p_start.add_argument("--mode", choices=["explore", "frontier", "rq", "project"], default="explore")
    p_start.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    p_start.set_defaults(func=start_session)

    p_add = sub.add_parser("add", help="Create an idea card.")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--summary", default="")
    p_add.add_argument("--domain", default="")
    p_add.add_argument("--session", default="")
    p_add.add_argument("--next-action", default="")
    p_add.add_argument("--frontier-needed", action="store_true")
    p_add.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    p_add.add_argument("--overwrite", action="store_true")
    p_add.set_defaults(func=add_idea)

    p_status = sub.add_parser("status", help="Show Idea Lab status.")
    p_status.set_defaults(func=status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

