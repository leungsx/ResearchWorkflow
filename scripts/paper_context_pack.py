#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
PROJECTS = ROOT / "projects"
BRIEF_DIR = ROOT / "vault" / "15_CNKI_Frontier" / "paper_briefs"


def load_rows(matrix: Path) -> list[dict[str, str]]:
    if not matrix.exists():
        return []
    with matrix.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_row(rows: list[dict[str, str]], citekey: str) -> dict[str, str]:
    for row in rows:
        if row.get("citekey") == citekey:
            return row
    raise KeyError(f"Citekey not found: {citekey}")


def project_rows(rows: list[dict[str, str]], project: str, only_read: bool) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in rows:
        tags = {tag.strip() for tag in (row.get("project_tags") or "").split(";") if tag.strip()}
        if project not in tags:
            continue
        if only_read and (row.get("read_status") or "") not in {"skimmed", "human-read", "verified"}:
            continue
        selected.append(row)
    return selected


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def truncate(text: str, max_chars: int) -> str:
    text = clean(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def compact_markdown(text: str, max_chars: int) -> str:
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "\n..."


def section(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group("body").strip() if match else ""


def bank_card(text: str, citekey: str) -> str:
    pattern = rf"^### `{re.escape(citekey)}`(?P<body>.*?)(?=^### `|\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    if not match:
        return ""
    return f"### `{citekey}`{match.group('body')}".strip()


def parse_blocks(reader: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    pattern = r"^### (?P<bid>B\d{4})\s*\n(?P<body>.*?)(?=^### B\d{4}\s*$|^## |\Z)"
    for match in re.finditer(pattern, reader, flags=re.M | re.S):
        block_id = match.group("bid")
        body = match.group("body")
        body = re.sub(r"^- Source ID:.*$", "", body, flags=re.M)
        body = re.sub(r"^- Page:.*$", "", body, flags=re.M)
        blocks[block_id] = body.strip()
    return blocks


def referenced_block_ids(*texts: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for text in texts:
        for block_id in re.findall(r"B\d{4}", text or ""):
            if block_id not in seen:
                seen.add(block_id)
                ordered.append(block_id)
    return ordered


def bulletize_excerpt(title: str, text: str, max_chars: int = 1200) -> list[str]:
    text = text.strip()
    if not text:
        return [f"## {title}", "", "未找到。", ""]
    return [f"## {title}", "", compact_markdown(text, max_chars), ""]


def render_pack(project: str, row: dict[str, str], reader: str, brief: str, bank: str, max_blocks: int, snippet_chars: int) -> str:
    citekey = row.get("citekey", "")
    title = row.get("title", "")
    reading_notes = section(reader, "Reading Notes")
    brief_understanding = section(brief, "全文级理解") or section(brief, "摘要级理解")
    brief_questions = section(brief, "研讨问题")
    brief_evidence = section(brief, "可用证据锚点")
    card = bank_card(bank, citekey)
    blocks = parse_blocks(reader)

    refs = referenced_block_ids(reading_notes, brief_evidence, card)
    if not refs:
        refs = list(blocks)[:max_blocks]
    refs = refs[:max_blocks]

    lines: list[str] = [
        f"# 论文带读上下文包 - {title}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Project: `{project}`",
        f"Citekey: `{citekey}`",
        f"Read status: `{row.get('read_status') or 'blank'}`",
        "",
        "## 用途",
        "",
        "这是共读时优先加载的小上下文包，用来节省 token。它只保留带读所需的压缩信息、证据 block 索引和少量原文片段。",
        "",
        "- 先用本文件带读论文核心内容。",
        "- 需要核验证据、补页码或处理细节时，再打开完整 Reader。",
        "- 本文件不替代原文，也不把论文自动标记为 `human-read` 或 `verified`。",
        "",
        "## 元数据",
        "",
        f"- 题名: {title or '未记录'}",
        f"- 作者: {row.get('authors') or '未记录'}",
        f"- 年份: {row.get('year') or '未记录'}",
        f"- 来源: {row.get('source') or '未记录'}",
        f"- 数据库: {row.get('source_database') or '未记录'}",
        f"- Reader: `{row.get('note_path') or '未记录'}`",
        f"- 原文: `{row.get('pdf_path') or '未记录'}`",
        "",
    ]
    lines.extend(bulletize_excerpt("Reader Reading Notes", reading_notes, 1800))
    lines.extend(bulletize_excerpt("研讨卡核心理解", brief_understanding, 1500))
    lines.extend(bulletize_excerpt("研讨问题", brief_questions, 1000))
    lines.extend(bulletize_excerpt("创新-局限-机会摘录", card, 2200))

    lines.extend(["## 核心证据 block 快照", ""])
    if not refs:
        lines.extend(["未找到可用 block。", ""])
    for block_id in refs:
        snippet = truncate(blocks.get(block_id, ""), snippet_chars)
        source_id = f"{citekey}:{block_id}"
        lines.extend([f"### {block_id}", "", f"- Source ID: `{source_id}`", f"- Snapshot: {snippet or '未找到。'}", ""])

    lines.extend(
        [
            "## 带读顺序",
            "",
            "1. 先用一句话判断它在本项目里的角色。",
            "2. 解释研究问题、对象、方法和核心结论。",
            "3. 只打开与核心结论有关的 block，避免全文漫游。",
            "4. 归纳创新点、关键局限和可转化研究问题。",
            "5. 和已读文献对比，更新综述或创新-局限台账。",
            "",
            "## 下次对 Codex 说",
            "",
            f"`基于 {citekey} 的上下文包带我复盘这篇论文，并指出它对我的研究有什么用。`",
            "",
        ]
    )
    return "\n".join(lines)


def output_path(project: str, citekey: str, output: Path | None) -> Path:
    if output:
        return output
    return PROJECTS / project / "literature" / "context_packs" / f"{citekey}.md"


def build_one(project: str, row: dict[str, str], output: Path | None, max_blocks: int, snippet_chars: int) -> Path:
    citekey = row.get("citekey", "")
    reader_path = Path(row.get("note_path") or PROJECTS / project / "literature" / "readers" / citekey / "paper.md")
    brief_path = BRIEF_DIR / f"{citekey}.md"
    bank_path = PROJECTS / project / "literature" / "innovation_limitation_bank.md"

    out = output_path(project, citekey, output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_pack(
            project=project,
            row=row,
            reader=read_text(reader_path),
            brief=read_text(brief_path),
            bank=read_text(bank_path),
            max_blocks=max_blocks,
            snippet_chars=snippet_chars,
        ),
        encoding="utf-8",
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build token-light paper context packs for guided reading.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--citekey", default="")
    parser.add_argument("--all-skimmed", action="store_true", help="Build packs for all skimmed/human-read/verified papers in the project.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-blocks", type=int, default=8)
    parser.add_argument("--snippet-chars", type=int, default=260)
    args = parser.parse_args()

    rows = load_rows(args.matrix)
    if args.all_skimmed:
        targets = project_rows(rows, args.project, only_read=True)
        if not targets:
            raise SystemExit(f"No skimmed/human-read/verified rows found for project: {args.project}")
    else:
        if not args.citekey:
            raise SystemExit("Use --citekey or --all-skimmed.")
        targets = [find_row(rows, args.citekey)]

    written: list[Path] = []
    for row in targets:
        written.append(build_one(args.project, row, args.output if len(targets) == 1 else None, args.max_blocks, args.snippet_chars))

    for path in written:
        print(f"Wrote paper context pack: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
