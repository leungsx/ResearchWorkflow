#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
OUT_DIR = ROOT / "vault" / "15_CNKI_Frontier" / "digests"

DEFAULT_FRONTIER_TERMS = [
    "生成式人工智能",
    "大语言模型",
    "人工智能",
    "智能体",
    "智慧图书馆",
    "知识服务",
    "数据要素",
    "公共数据",
    "数据治理",
    "数据可信空间",
    "数字学术",
    "情报服务",
    "新质生产力",
    "十五五",
    "知识组织",
    "信息资源管理",
]


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    return re.sub(r"-+", "-", value).strip("-") or "cnki-frontier"


def split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return [term.strip() for term in re.split(r"[,，;；、\n]+", value) if term.strip()]


def load_rows(matrix: Path) -> list[dict[str, str]]:
    if not matrix.exists():
        return []
    with matrix.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def year_int(row: dict[str, str]) -> int:
    try:
        return int(row.get("year", "") or 0)
    except ValueError:
        return 0


def text_blob(row: dict[str, str]) -> str:
    fields = [
        "title",
        "source",
        "core_findings",
        "theory",
        "methods",
        "data",
        "target_journal_relevance",
        "cssci_status",
    ]
    return "\n".join(row.get(field, "") for field in fields)


def score_row(row: dict[str, str], terms: list[str], current_year: int) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    year = year_int(row)
    if year >= current_year:
        score += 30
        reasons.append("当年文献")
    elif year == current_year - 1:
        score += 24
        reasons.append("近一年文献")
    elif year == current_year - 2:
        score += 16
        reasons.append("近两年文献")
    elif year:
        score += max(0, 10 - (current_year - year))

    blob = text_blob(row)
    hit_terms = [term for term in terms if term and term in blob]
    if hit_terms:
        score += min(40, 8 * len(hit_terms))
        reasons.append("命中前沿词: " + "、".join(hit_terms[:5]))

    source = row.get("source", "")
    if "图书情报工作" in source:
        score += 12
        reasons.append("目标刊或近邻来源")

    cssci = row.get("cssci_status", "")
    if "CSSCI" in cssci.upper():
        score += 10
        reasons.append("CSSCI")
    elif "核心" in cssci:
        score += 6
        reasons.append("核心来源")

    if row.get("target_journal_relevance", "").strip():
        score += 10
        reasons.append("已标注目标刊相关性")

    if row.get("read_status", "") in {"metadata-only", "unread", ""}:
        score += 3
        reasons.append("尚未阅读")

    return score, reasons


def summarize_metadata(row: dict[str, str]) -> str:
    abstract = row.get("core_findings", "").strip()
    if not abstract:
        return "暂无摘要信息；只能根据题名和来源判断，需补充 CNKI 摘要或全文。"
    abstract = re.sub(r"\s+", " ", abstract)
    return abstract[:220] + ("..." if len(abstract) > 220 else "")


def method_hint(row: dict[str, str]) -> str:
    text = (row.get("methods", "") + "\n" + row.get("core_findings", "") + "\n" + row.get("title", "")).lower()
    mapping = [
        ("问卷", "可能包含问卷调查"),
        ("访谈", "可能包含访谈或质性材料"),
        ("案例", "可能是案例研究"),
        ("实证", "可能有实证分析"),
        ("模型", "可能构建模型或框架"),
        ("网络", "可能涉及网络分析"),
        ("计量", "可能涉及文献计量或统计分析"),
        ("内容分析", "可能涉及内容分析"),
        ("综述", "可能是综述述评"),
    ]
    hits = [label for key, label in mapping if key in text]
    return "；".join(hits) if hits else "需读方法部分后确认。"


def novelty_hint(row: dict[str, str], terms: list[str]) -> str:
    blob = text_blob(row)
    hits = [term for term in terms if term in blob]
    if hits:
        return "可能围绕 " + "、".join(hits[:4]) + " 提供新情境、新框架或新应用。需全文验证。"
    return "从元数据看创新点尚不明确，建议先看引言和结论。"


def render_digest(
    rows: list[dict[str, str]],
    selected: list[tuple[int, list[str], dict[str, str]]],
    topic: str,
    terms: list[str],
    tag: str,
    limit: int,
    matrix: Path,
) -> str:
    today = dt.date.today().isoformat()
    lines = [
        f"# CNKI 前沿雷达 - {today}",
        "",
        f"Topic: {topic or '未指定'}",
        f"Project tag: `{tag or 'all'}`",
        f"Source matrix: `{matrix}`",
        f"Candidate pool: {len(rows)} CNKI rows",
        f"Selected: {len(selected)} / {limit}",
        "",
        "## 使用边界",
        "",
        "- 这是基于 CNKI 导出元数据和文献矩阵的前沿雷达，不等于全文阅读。",
        "- `metadata-only` 文献只能做摘要级判断；真正用于论文论证前必须读全文。",
        "- 原文 PDF/CAJ 只能来自你有合法访问权限的 CNKI 下载或机构资源。",
        "",
        "## 今日建议",
        "",
    ]

    if not selected:
        lines.extend(
            [
                "当前没有可用于雷达的 CNKI 行。",
                "",
                "建议先在 CNKI 按以下方向检索并导出 CSV/RIS/EndNote 文本：",
                "",
                "- " + " OR ".join(terms[:8]),
                "",
                "导入命令：",
                "",
                "```bash",
                "make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug>",
                "make cnki-frontier TAG=<project_slug>",
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    top = selected[0][2]
    lines.append(f"- 优先研讨：`{top.get('citekey')}` 《{top.get('title')}》。")
    if len(selected) > 1:
        lines.append(f"- 备选精读：`{selected[1][2].get('citekey')}` 《{selected[1][2].get('title')}》。")
    lines.append("- 今日目标不是读完所有文献，而是识别 1 篇值得全文精读的论文。")
    lines.extend(["", "## 候选文献总览", "", "| Rank | Score | Citekey | Year | Title | Source | Why selected |", "|---:|---:|---|---:|---|---|---|"])

    for rank, (score, reasons, row) in enumerate(selected, start=1):
        lines.append(
            f"| {rank} | {score} | `{row.get('citekey')}` | {row.get('year')} | {row.get('title')} | {row.get('source')} | {'；'.join(reasons)} |"
        )

    lines.extend(["", "## 逐篇研讨卡", ""])
    for rank, (score, reasons, row) in enumerate(selected, start=1):
        lines.extend(
            [
                f"### {rank}. {row.get('title')}",
                "",
                f"- Citekey: `{row.get('citekey')}`",
                f"- 年份/来源: {row.get('year')} / {row.get('source')}",
                f"- 作者: {row.get('authors') or '未记录'}",
                f"- 质量信号: {row.get('cssci_status') or '未标注'}",
                f"- 选择理由: {'；'.join(reasons)}",
                f"- 摘要级概括: {summarize_metadata(row)}",
                f"- 可能创新点: {novelty_hint(row, terms)}",
                f"- 方法线索: {method_hint(row)}",
                "- 可以讨论的问题:",
                "  - 这篇文献的问题意识是否贴近《图书情报工作》的信息资源管理语境？",
                "  - 它的方法是可以借鉴、可以复现，还是只适合作为背景引用？",
                "  - 它与我的潜在研究问题是互补、重复，还是构成反例？",
                "- 下一步:",
                f"  - 快读卡: `make paper-brief CITEKEY={row.get('citekey')}`",
                "  - 若值得精读：下载授权全文，填入 `pdf_path`，再做全文 reader。",
                "",
            ]
        )

    lines.extend(
        [
            "## 今日输出决策",
            "",
            "- [ ] 选出 1 篇全文精读。",
            "- [ ] 给 1-2 篇更新 `target_journal_relevance`。",
            "- [ ] 把明显无关文献标记为 `read_status=discarded` 或保留为背景。",
            "- [ ] 对有价值文献补充 PDF 路径和阅读状态。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a CNKI frontier digest from literature_matrix.csv.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--tag", default="", help="Filter project_tags by substring")
    parser.add_argument("--topic", default="", help="Human-readable digest topic")
    parser.add_argument("--keywords", default="", help="Extra keywords separated by comma/semicolon")
    parser.add_argument("--limit", type=int, default=7)
    parser.add_argument("--since-year", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    current_year = dt.date.today().year
    terms = split_terms(args.keywords) + DEFAULT_FRONTIER_TERMS
    rows = [
        row
        for row in load_rows(args.matrix)
        if row.get("source_database", "").upper() == "CNKI"
        and (not args.tag or args.tag in row.get("project_tags", ""))
        and (not args.since_year or year_int(row) >= args.since_year)
    ]
    ranked = []
    for row in rows:
        score, reasons = score_row(row, terms, current_year)
        ranked.append((score, reasons, row))
    ranked.sort(key=lambda item: (item[0], year_int(item[2])), reverse=True)
    selected = ranked[: max(1, args.limit)]

    output = args.output
    if output is None:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{dt.date.today().isoformat()}-{slugify(args.topic or args.tag or 'cnki-frontier')}.md"
        output = OUT_DIR / name
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_digest(rows, selected, args.topic, terms, args.tag, args.limit, args.matrix), encoding="utf-8")
    print(f"Wrote CNKI frontier digest: {output}")
    print(f"Selected papers: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
