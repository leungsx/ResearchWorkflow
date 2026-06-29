#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"
BANK_NAME = "innovation_limitation_bank.md"


def read_matrix(project: str) -> list[dict[str, str]]:
    if not MATRIX.exists():
        return []
    with MATRIX.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if project in row.get("project_tags", "")]


def find_row(rows: list[dict[str, str]], citekey: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("citekey") == citekey:
            return row
    return None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def bank_path(project: str) -> Path:
    return PROJECTS / project / "literature" / BANK_NAME


def skeleton(project: str) -> str:
    today = dt.date.today().isoformat()
    return f"""# {project}：创新点、局限性与机会台账

Project: `{project}`
Created: {today}
Purpose: 主读论文后沉淀可复用创新、关键局限和可转化研究机会。

## 使用规则

- 只记录已经 source-grounded 阅读过的论文。
- 每条判断都补 reader block ID 或页码；没有证据定位时只写成待核验。
- 机会要说明来自哪类创新或局限，避免把一般启发直接写成选题。

## 已读论文卡片
"""


def ensure_bank(project: str) -> Path:
    path = bank_path(project)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(skeleton(project), encoding="utf-8")
    return path


def card_count(text: str) -> int:
    return len(re.findall(r"^### `(?!<)[^`]+` - ", text, flags=re.MULTILINE))


def has_card(text: str, citekey: str) -> bool:
    return bool(re.search(rf"^### `{re.escape(citekey)}`\b", text, flags=re.MULTILINE))


def card_template(project: str, row: dict[str, str]) -> str:
    citekey = row.get("citekey", "")
    title = row.get("title", "")
    source = ", ".join(item for item in [row.get("source", ""), row.get("year", "")] if item)
    status = row.get("read_status", "") or "unread"
    note_path = row.get("note_path", "")
    reader = rel(Path(note_path)) if note_path else f"projects/{project}/literature/readers/{citekey}/paper.md"
    return f"""
### `{citekey}` - {title}

- Source: {source or "待补"}
- Read status: `{status}`
- Reader: `{reader}`
- 证据边界: 待补。

#### 可复用创新点

| 类型 | 创新点 | 证据定位 | 可迁移价值 | 机会编号 |
|---|---|---|---|---|
|  |  |  |  |  |

#### 关键局限性

| 类型 | 局限性 | 证据定位 | 可转化研究或改进点 | 优先级 |
|---|---|---|---|---|
|  |  |  |  |  |

#### 可转化研究问题

- RQ-:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create/check the project innovation-limitation-opportunity bank.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--citekey", help="Append a blank insight card for this literature_matrix citekey if missing.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be appended without writing.")
    args = parser.parse_args()

    path = ensure_bank(args.project)
    text = path.read_text(encoding="utf-8")

    if not args.citekey:
        print(f"Insight bank: {path}")
        print(f"Cards: {card_count(text)}")
        return 0

    if has_card(text, args.citekey):
        print(f"Insight card already exists: {args.citekey}")
        print(f"Insight bank: {path}")
        return 0

    rows = read_matrix(args.project)
    row = find_row(rows, args.citekey)
    if row is None:
        raise SystemExit(f"citekey not found for project {args.project}: {args.citekey}")

    template = card_template(args.project, row)
    if args.dry_run:
        print(template.lstrip())
        return 0

    path.write_text(text.rstrip() + "\n" + template, encoding="utf-8")
    print(f"Appended insight card template: {args.citekey}")
    print(f"Insight bank: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
