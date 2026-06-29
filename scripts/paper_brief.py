#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
OUT_DIR = ROOT / "vault" / "15_CNKI_Frontier" / "paper_briefs"


def load_rows(matrix: Path) -> list[dict[str, str]]:
    if not matrix.exists():
        return []
    with matrix.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_row(rows: list[dict[str, str]], citekey: str, title: str) -> dict[str, str]:
    if citekey:
        for row in rows:
            if row.get("citekey") == citekey:
                return row
        raise KeyError(f"Citekey not found: {citekey}")
    if title:
        candidates = [row for row in rows if title in row.get("title", "")]
        if len(candidates) == 1:
            return candidates[0]
        if not candidates:
            raise KeyError(f"Title not found: {title}")
        raise KeyError(f"Multiple title matches found; use --citekey. Matches: {[row.get('citekey') for row in candidates]}")
    raise ValueError("Use --citekey or --title.")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def snippet(text: str, n: int = 280) -> str:
    text = clean(text)
    if not text:
        return "未记录。"
    return text[:n] + ("..." if len(text) > n else "")


def method_guess(row: dict[str, str]) -> str:
    text = clean("\n".join([row.get("title", ""), row.get("methods", ""), row.get("core_findings", "")]))
    rules = [
        ("实证", "实证研究"),
        ("问卷", "问卷调查"),
        ("访谈", "访谈研究"),
        ("案例", "案例研究"),
        ("内容分析", "内容分析"),
        ("文献计量", "文献计量"),
        ("网络分析", "网络分析"),
        ("模型", "模型/框架构建"),
        ("综述", "综述述评"),
        ("演化", "演化分析"),
        ("评价", "评价研究"),
    ]
    hits = [label for key, label in rules if key in text]
    return "；".join(hits) if hits else "仅凭元数据无法确认，需要读方法部分。"


def original_access(row: dict[str, str], pdf: str) -> str:
    path = pdf or row.get("pdf_path", "")
    if path:
        return f"本地原文路径：`{path}`。请确认该文件来自你有合法访问权限的 CNKI/机构资源。"
    return "尚未记录本地原文。请在 CNKI 合法下载 PDF/可转换全文后，把路径写入 `pdf_path`，再升级为全文精读。"


def render(row: dict[str, str], pdf: str) -> str:
    citekey = row.get("citekey", "")
    title = row.get("title", "")
    source_level = "全文可用" if (pdf or row.get("pdf_path")) else "摘要/元数据级"
    lines = [
        f"# 论文研讨卡 - {title}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Citekey: `{citekey}`",
        f"Source level: {source_level}",
        "",
        "## 元数据",
        "",
        f"- 题名：{title}",
        f"- 作者：{row.get('authors') or '未记录'}",
        f"- 年份：{row.get('year') or '未记录'}",
        f"- 来源：{row.get('source') or '未记录'}",
        f"- 数据库：{row.get('source_database') or '未记录'}",
        f"- CSSCI/核心状态：{row.get('cssci_status') or '未标注'}",
        f"- DOI：{row.get('doi') or '未记录'}",
        f"- 阅读状态：{row.get('read_status') or '未记录'}",
        "",
        "## 摘要级理解",
        "",
        f"- 摘要/关键词：{snippet(row.get('core_findings', ''))}",
        f"- 一句话概括：这篇文章大概率围绕“{title}”所指问题展开；当前判断基于元数据，需全文验证。",
        f"- 可能创新点：{row.get('target_journal_relevance') or '尚未人工标注；建议读引言、文献综述和结论确认。'}",
        f"- 研究方法线索：{method_guess(row)}",
        f"- 与常规研究不一样的点：需对比同主题近 3-5 篇文献后判断，不能仅凭题名下结论。",
        "",
        "## 研讨问题",
        "",
        "- 它真正解决的是理论问题、方法问题，还是实践场景问题？",
        "- 它的数据或案例是否能支撑结论，还是更像概念性讨论？",
        "- 它对我的研究是背景、方法借鉴、反例，还是潜在竞争文献？",
        "- 如果投《图书情报工作》，它提示我需要补强哪类贡献？",
        "",
        "## 原文与精读升级",
        "",
        original_access(row, pdf),
        "",
        "升级为全文 reader 的标准：",
        "",
        "- 有合法获取的 PDF 或可转换全文。",
        "- 不只总结摘要，而是抽取全文结构、图表、方法、局限和可引用证据。",
        "- 输出 `paper.md`、`source_map.json`、`translation_notes.md` 和必要 assets。",
        "",
        "## 待补充",
        "",
        "- [ ] 是否已读全文？",
        "- [ ] 可引用证据有哪些？",
        "- [ ] 方法是否可复用？",
        "- [ ] 与我的项目/论文主张如何连接？",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a one-paper discussion card from the literature matrix.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--citekey", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--pdf", default="", help="Optional local full-text PDF path")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    row = find_row(load_rows(args.matrix), args.citekey, args.title)
    output = args.output
    if output is None:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        output = OUT_DIR / f"{row.get('citekey')}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(row, args.pdf), encoding="utf-8")
    print(f"Wrote paper discussion card: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
