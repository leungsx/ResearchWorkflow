#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
CONCEPTS = VAULT / "02_Concepts"
METHODS = VAULT / "03_Methods"
LEARNING = VAULT / "12_Learning_Log"
SESSIONS = LEARNING / "sessions"
GRAPH = VAULT / "13_Knowledge_Graph"
REVIEW = VAULT / "14_Review_Queue"
KNOWLEDGE_INDEX = GRAPH / "knowledge_index.csv"
REVIEW_QUEUE = REVIEW / "review_queue.csv"


INDEX_FIELDS = [
    "id",
    "title",
    "type",
    "domain",
    "level",
    "created_at",
    "status",
    "next_review",
    "note_path",
]

REVIEW_FIELDS = [
    "id",
    "title",
    "type",
    "stage",
    "next_review",
    "prompt",
    "note_path",
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w._-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "knowledge"


def ensure_csv(path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()


def append_csv(path: Path, fields: list[str], row: dict[str, str]) -> None:
    ensure_csv(path, fields)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow(row)


def next_review_date() -> str:
    return (dt.date.today() + dt.timedelta(days=1)).isoformat()


def write_note(path: Path, content: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Note already exists: {path}")
    path.write_text(content, encoding="utf-8")


def concept(args: argparse.Namespace) -> int:
    slug = slugify(args.title)
    note_id = f"concept-{slug}"
    path = CONCEPTS / f"{slug}.md"
    links = "\n".join(f"- [[{item.strip()}]]" for item in args.links.split(",") if item.strip())
    content = f"""---
type: concept
id: {note_id}
title: "{args.title}"
domain: "{args.domain or ''}"
level: "{args.level}"
status: learning
review_stage: 1
next_review: {next_review_date()}
---

# {args.title}

## 一句话解释

{args.summary or ''}

## 通俗解释

## 生活/科研例子

## 为什么它对我的研究重要

## 容易误解的地方

## 和哪些概念相关

{links}

## 和哪些方法相关

## 我自己的理解

## 复习问题

1. 这个概念解决什么问题？
2. 它和相近概念有什么区别？
3. 我能在自己的研究中怎么用它？

## 研究灵感

"""
    write_note(path, content, args.overwrite)
    append_csv(
        KNOWLEDGE_INDEX,
        INDEX_FIELDS,
        {
            "id": note_id,
            "title": args.title,
            "type": "concept",
            "domain": args.domain or "",
            "level": args.level,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "status": "learning",
            "next_review": next_review_date(),
            "note_path": str(path),
        },
    )
    append_csv(
        REVIEW_QUEUE,
        REVIEW_FIELDS,
        {
            "id": note_id,
            "title": args.title,
            "type": "concept",
            "stage": "1",
            "next_review": next_review_date(),
            "prompt": f"用自己的话解释 {args.title}，并举一个科研例子。",
            "note_path": str(path),
        },
    )
    print(f"Created concept note: {path}")
    return 0


def method(args: argparse.Namespace) -> int:
    slug = slugify(args.title)
    note_id = f"method-{slug}"
    path = METHODS / f"{slug}.md"
    links = "\n".join(f"- [[{item.strip()}]]" for item in args.links.split(",") if item.strip())
    content = f"""---
type: method
id: {note_id}
title: "{args.title}"
domain: "{args.domain or ''}"
level: "{args.level}"
status: learning
review_stage: 1
next_review: {next_review_date()}
---

# {args.title}

## 一句话用途

{args.summary or ''}

## 它解决什么科研问题

## 通俗解释

## 适用场景

## 不适用场景

## 输入数据

## 操作步骤

## 输出结果怎么解释

## 常见错误

## 和哪些概念相关

{links}

## Python / R / MATLAB 实现

## 论文中怎么写

## 复习问题

1. 这个方法回答哪类问题？
2. 它有哪些前提假设？
3. 如果结果不符合预期，可能是什么原因？

## 研究灵感

"""
    write_note(path, content, args.overwrite)
    append_csv(
        KNOWLEDGE_INDEX,
        INDEX_FIELDS,
        {
            "id": note_id,
            "title": args.title,
            "type": "method",
            "domain": args.domain or "",
            "level": args.level,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "status": "learning",
            "next_review": next_review_date(),
            "note_path": str(path),
        },
    )
    append_csv(
        REVIEW_QUEUE,
        REVIEW_FIELDS,
        {
            "id": note_id,
            "title": args.title,
            "type": "method",
            "stage": "1",
            "next_review": next_review_date(),
            "prompt": f"说明 {args.title} 适合解决什么问题、有什么前提假设。",
            "note_path": str(path),
        },
    )
    print(f"Created method note: {path}")
    return 0


def session(args: argparse.Namespace) -> int:
    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    slug = slugify(args.topic)
    path = SESSIONS / f"{day.isoformat()}-{slug}.md"
    content = f"""# Learning Session - {args.topic}

Date: {day.isoformat()}
Topic: {args.topic}

## 用户原始问题

{args.question or ''}

## 通俗解释

## 科研例子

## 关键概念

## 关键方法

## 易错点

## 我是否真的理解了

## 需要创建/更新的知识卡片

## 复习任务

## 可能引出的研究灵感

"""
    write_note(path, content, args.overwrite)
    print(f"Created learning session: {path}")
    return 0


def status(_: argparse.Namespace) -> int:
    ensure_csv(KNOWLEDGE_INDEX, INDEX_FIELDS)
    ensure_csv(REVIEW_QUEUE, REVIEW_FIELDS)
    concept_count = len([p for p in CONCEPTS.glob("*.md") if p.is_file()])
    method_count = len([p for p in METHODS.glob("*.md") if p.is_file()])
    session_count = len([p for p in SESSIONS.glob("*.md") if p.is_file()])
    print("# Knowledge Coach Status\n")
    print(f"- Concept notes: {concept_count}")
    print(f"- Method notes: {method_count}")
    print(f"- Learning sessions: {session_count}")
    print(f"- Knowledge index: {KNOWLEDGE_INDEX}")
    print(f"- Review queue: {REVIEW_QUEUE}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create learning notes, method cards, and review records.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_concept = sub.add_parser("concept", help="Create a concept note.")
    p_concept.add_argument("--title", required=True)
    p_concept.add_argument("--summary", default="")
    p_concept.add_argument("--domain", default="")
    p_concept.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    p_concept.add_argument("--links", default="")
    p_concept.add_argument("--overwrite", action="store_true")
    p_concept.set_defaults(func=concept)

    p_method = sub.add_parser("method", help="Create a research method note.")
    p_method.add_argument("--title", required=True)
    p_method.add_argument("--summary", default="")
    p_method.add_argument("--domain", default="")
    p_method.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    p_method.add_argument("--links", default="")
    p_method.add_argument("--overwrite", action="store_true")
    p_method.set_defaults(func=method)

    p_session = sub.add_parser("session", help="Create a learning session note.")
    p_session.add_argument("--topic", required=True)
    p_session.add_argument("--question", default="")
    p_session.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    p_session.add_argument("--overwrite", action="store_true")
    p_session.set_defaults(func=session)

    p_status = sub.add_parser("status", help="Show knowledge coach status.")
    p_status.set_defaults(func=status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
