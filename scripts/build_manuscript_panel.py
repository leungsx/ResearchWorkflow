#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def section(text: str, heading: str) -> str:
    pattern = rf"(?ms)^##+ {re.escape(heading)}\s*\n(.*?)(?=^##+ |\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def current_questions(project: Path) -> list[str]:
    text = read_text(project / "01_research_question.md")
    block = section(text, "Converged Main Question")
    if not block:
        block = section(text, "Current Preferred Direction")
    questions: list[str] = []
    for line in block.splitlines():
        if "question:" in line.lower() or line.startswith("Sub-question"):
            questions.append(clean(line.lstrip("- ")))
    return questions[:4]


def evidence_summary(project: Path) -> tuple[int, int, int]:
    path = project / "literature" / "evidence_locator_table.csv"
    if not path.exists():
        return 0, 0, 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    located = sum(1 for row in rows if clean(row.get("page", "")))
    pending = len(rows) - located
    return len(rows), located, pending


def md_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    lines = []
    lines.append("| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(rows[0])) + " |")
    lines.append("| " + " | ".join("-" * widths[index] for index in range(len(rows[0]))) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) + " |")
    return lines


def render_md(project_slug: str, project: Path) -> str:
    questions = current_questions(project)
    rows, located, pending = evidence_summary(project)
    lines = [
        "# Manuscript Production Panel",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Project: `{project_slug}`",
        "",
        "## Current Manuscript Direction",
        "",
    ]
    if questions:
        for question in questions:
            lines.append(f"- {question}")
    else:
        lines.append("- 待从 `01_research_question.md` 收敛主问题。")
    lines.extend(
        [
            "",
            "## Working Conceptual Chain",
            "",
            "`platform engagement -> service touchpoint -> reading-promotion outcome`",
            "",
            "- SICAS explains the user path from sense/interest to action/share.",
            "- AARRR organizes lifecycle indicators, but must be translated into library-service outcomes.",
            "- Propagation-power metrics describe visibility and interaction; they do not alone prove service value.",
            "",
            "## Variable And Indicator Draft",
            "",
        ]
    )
    lines.extend(
        md_table(
            [
                ["Layer", "Candidate indicators", "Current evidence", "Risk before writing"],
                ["Platform engagement", "粉丝量、发布量、点赞/评论/转发、爆款指数、DCI/传播力指数", "传播力评价、DCI、爆款指数相关 Readers", "容易把平台热度误写成服务价值"],
                ["Service touchpoint", "资源入口、活动入口、咨询/连接路径、线上线下转换、服务信息清晰度", "SICAS、AARRR、数字阅读推广与营销策略文献", "服务触达仍需可观察指标"],
                ["Reading outcome", "阅读参与、资源访问、活动报名、读者反馈、知识传播效果", "目前多为框架启发，直接证据不足", "需要后续数据或更强文献补证"],
                ["Boundary", "馆型差异、平台差异、时间窗口、账号规模", "公共馆/高校馆比较、平台适配文献", "不能用单平台结论外推所有馆型"],
            ]
        )
    )
    lines.extend(
        [
            "",
            "## Evidence Readiness",
            "",
            f"- Locator rows: {rows}",
            f"- Page located: {located}",
            f"- Page pending: {pending}",
            "",
            "## Paragraph Queue",
            "",
            "- Literature gap paragraph: existing studies measure visibility and interaction more readily than service-value outcomes.",
            "- Framework paragraph: separate platform engagement, service touchpoint, and reading-promotion outcome before combining indicators.",
            "- Method paragraph: use source-grounded literature to draft variables, then require page/table verification before citation.",
            "- Boundary paragraph: current evidence is mostly descriptive/correlational and 2019-2021 heavy; causal and current-platform claims need new data.",
            "",
            "## Next Writing Actions",
            "",
            "- Verify page/table locators for the current evidence rows marked `page_pending`.",
            "- Upgrade the strongest propagation/service-value papers from `skimmed` to `human-read` only after real reading.",
            "- Fill `07_claim_evidence_map.md` with 3-5 draft claims before writing the introduction and literature review.",
            "- Keep metadata-only papers out of manuscript claims until they have a Reader or full-text note.",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(project_slug: str, md_text: str, html_path: Path, md_path: Path) -> str:
    lines = md_text.splitlines()
    body_parts: list[str] = []
    in_table = False
    for line in lines:
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if in_table:
                body_parts.append("</tbody></table>")
                in_table = False
            body_parts.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("| ") and "---" in line:
            continue
        elif line.startswith("- "):
            body_parts.append(f"<p class=\"bullet\">{html.escape(line[2:])}</p>")
        elif line.startswith("`") and line.endswith("`"):
            body_parts.append(f"<p><code>{html.escape(line.strip('`'))}</code></p>")
        elif line.startswith("| "):
            cells = [html.escape(cell.strip()) for cell in line.strip().strip("|").split("|")]
            if not in_table:
                header = "".join(f"<th>{cell}</th>" for cell in cells)
                body_parts.append(f"<table><thead><tr>{header}</tr></thead><tbody>")
                in_table = True
            else:
                body_parts.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        elif clean(line):
            body_parts.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body_parts.append("</tbody></table>")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>论文写作推进面板 - {html.escape(project_slug)}</title>
  <style>
    :root {{ --ink:#1e293b; --muted:#64748b; --line:#dbe4ee; --paper:#fff; --soft:#f8fafc; --blue:#2563eb; --shadow:0 10px 28px rgba(15,23,42,.06); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:#f8fafc; line-height:1.65; }}
    header {{ background:#fff; border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:980px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:26px 0 10px; border-top:1px solid var(--line); padding-top:16px; font-size:21px; }}
    a {{ color:var(--blue); text-decoration:none; }}
    .sub {{ color:var(--muted); }}
    .panel {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:20px; box-shadow:var(--shadow); }}
    .bullet {{ margin-left:18px; }}
    .bullet::before {{ content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--blue); margin:0 8px 2px -16px; }}
    code {{ background:#eef3f8; border:1px solid #d8e2ec; border-radius:5px; padding:1px 4px; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; margin:10px 0 18px; }}
    th, td {{ text-align:left; vertical-align:top; border-bottom:1px solid var(--line); padding:9px 8px; }}
    th {{ color:var(--muted); font-weight:650; background:#fbfdff; }}
    @media (max-width:840px) {{ h1 {{ font-size:28px; }} table {{ display:block; overflow-x:auto; }} }}
  </style>
</head>
<body>
  <header><div class="wrap">
    <h1>论文写作推进面板</h1>
    <p class="sub">{html.escape(project_slug)} · Generated {html.escape(dt.datetime.now().isoformat(timespec='seconds'))}</p>
    <p><a href="../../../study_dashboard.html">返回学习仪表盘</a></p>
  </div></header>
  <main class="wrap"><article class="panel">
    {''.join(body_parts)}
  </article></main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a project manuscript production panel.")
    parser.add_argument("--project", default="library_short_video")
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    out_dir = project / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "writing_panel.md"
    html_path = out_dir / "writing_panel.html"
    md_text = render_md(args.project, project)
    md_path.write_text(md_text + "\n", encoding="utf-8")
    html_path.write_text(render_html(args.project, md_text, html_path, md_path), encoding="utf-8")
    print(f"Wrote manuscript panel markdown: {md_path}")
    print(f"Wrote manuscript panel HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
