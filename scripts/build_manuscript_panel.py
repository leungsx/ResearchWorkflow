#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
from pathlib import Path

from workflow_config import active_project_slug


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


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def claim_links(project: Path) -> list[dict[str, str]]:
    return csv_rows(project / "evidence" / "claim_evidence_links.csv")


def group_claims(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        claim_id = clean(row.get("claim_id", ""))
        if claim_id:
            grouped.setdefault(claim_id, []).append(row)
    return grouped


def row_trace(row: dict[str, str]) -> str:
    page = clean(row.get("page", "")) or "page pending"
    return f"{clean(row.get('source_block_id', ''))} / {page} / {clean(row.get('read_status', ''))}"


def readiness(rows: list[dict[str, str]]) -> str:
    accepted = {"human-read", "verified", "claim-linked", "manuscript-cited"}
    located = sum(1 for row in rows if clean(row.get("page", "")))
    human_ready = sum(1 for row in rows if clean(row.get("read_status", "")) in accepted)
    return f"{human_ready}/{len(rows)} human-ready; {located}/{len(rows)} page-located"


def claim_brief(rows: list[dict[str, str]], limit: int = 4) -> str:
    if not rows:
        return "No linked claim yet"
    grouped = group_claims(rows)
    labels = []
    for claim_id, claim_rows in list(grouped.items())[:limit]:
        labels.append(f"{claim_id} ({readiness(claim_rows)})")
    if len(grouped) > limit:
        labels.append(f"+{len(grouped) - limit} more")
    return "; ".join(labels)


def source_trace(rows: list[dict[str, str]], limit: int = 3) -> str:
    traces = [row_trace(row) for row in rows[:limit]]
    if len(rows) > limit:
        traces.append(f"+{len(rows) - limit} more")
    return "; ".join(traces) if traces else "No source trace yet"


def match_claim_rows(rows: list[dict[str, str]], keywords: list[str], limit: int = 8) -> list[dict[str, str]]:
    scored: list[tuple[int, str, dict[str, str]]] = []
    for row in rows:
        text = " ".join(
            [
                clean(row.get("claim_text", "")),
                clean(row.get("citekey", "")),
                clean(row.get("source_block_id", "")),
            ]
        ).lower()
        score = sum(1 for keyword in keywords if keyword.lower() in text)
        if score:
            scored.append((score, clean(row.get("claim_id", "")), row))
    scored.sort(key=lambda item: (-item[0], item[1], clean(item[2].get("source_block_id", ""))))
    selected: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for _score, _claim_id, row in scored:
        key = (clean(row.get("claim_id", "")), clean(row.get("source_block_id", "")))
        if key in seen:
            continue
        seen.add(key)
        selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def traceability_payload(project_slug: str, project: Path) -> dict[str, object]:
    rows = claim_links(project)
    grouped = group_claims(rows)
    located = sum(1 for row in rows if clean(row.get("page", "")))
    human_ready = sum(1 for row in rows if clean(row.get("read_status", "")) in {"human-read", "verified", "claim-linked", "manuscript-cited"})
    questions = current_questions(project)
    question_rules = [
        ("Main question", ["平台", "服务价值", "阅读推广", "传播力", "SICAS", "AARRR", "数字阅读"]),
        ("Sub-question 1", ["标题", "内容", "音乐", "互动", "行动", "SICAS", "Hook", "机制"]),
        ("Sub-question 2", ["公共图书馆", "高校图书馆", "平台", "差异", "馆型", "比较", "AARRR"]),
    ]
    question_traces = []
    for index, question in enumerate(questions[:3]):
        label, keywords = question_rules[index] if index < len(question_rules) else (f"Question {index + 1}", [])
        matched = match_claim_rows(rows, keywords or [question], limit=8)
        question_traces.append(
            {
                "slot": label,
                "question": question,
                "linked_claims": claim_brief(matched),
                "source_trace": source_trace(matched),
                "readiness": readiness(matched) if matched else "No linked claim yet",
            }
        )

    variable_rules = [
        {
            "layer": "Platform engagement",
            "indicators": "粉丝量、发布量、点赞/评论/转发、爆款指数、DCI/传播力指数、标题/音乐/内容形式",
            "keywords": ["粉丝", "发布", "点赞", "评论", "转发", "爆款", "DCI", "传播力", "标题", "音乐", "内容"],
            "boundary": "Can support visibility/interaction claims, not service-value claims alone.",
        },
        {
            "layer": "Service touchpoint",
            "indicators": "资源入口、活动入口、咨询/连接路径、线上线下转换、服务信息清晰度",
            "keywords": ["服务", "触达", "资源", "活动", "咨询", "线上线下", "渠道", "互动营销", "数字阅读"],
            "boundary": "Needs observable service path or library-service outcome before manuscript use.",
        },
        {
            "layer": "Reading-promotion outcome",
            "indicators": "阅读参与、资源访问、活动报名、读者反馈、知识传播效果、分享回流",
            "keywords": ["阅读", "服务价值", "行动", "分享", "资源", "活动", "知识传播", "SICAS"],
            "boundary": "Current corpus supports framework design; outcome measurement needs stronger data.",
        },
        {
            "layer": "Boundary and comparison",
            "indicators": "馆型、平台类型、时间窗口、账号规模、公共馆/高校馆/科研型图书馆差异",
            "keywords": ["公共图书馆", "高校图书馆", "馆型", "平台", "差异", "比较", "账号"],
            "boundary": "Do not generalize from one platform/time window to all library contexts.",
        },
    ]
    variable_traces = []
    for rule in variable_rules:
        matched = match_claim_rows(rows, list(rule["keywords"]), limit=8)
        variable_traces.append(
            {
                "layer": rule["layer"],
                "candidate_indicators": rule["indicators"],
                "linked_claims": claim_brief(matched),
                "source_trace": source_trace(matched),
                "boundary": rule["boundary"],
            }
        )

    paragraph_rules = [
        {
            "slot": "Literature gap paragraph",
            "purpose": "Explain why platform visibility needs to be separated from library service value.",
            "keywords": ["服务价值", "传播力", "数字阅读", "平台", "互动"],
            "next_action": "Verify page/table locators before turning this into a formal literature-review claim.",
        },
        {
            "slot": "Framework paragraph",
            "purpose": "Introduce platform engagement -> service touchpoint -> reading-promotion outcome.",
            "keywords": ["SICAS", "AARRR", "服务", "阅读推广", "行动", "分享"],
            "next_action": "Keep causal wording out until new data or verified source locators support it.",
        },
        {
            "slot": "Variable paragraph",
            "purpose": "Translate prior studies into candidate variables and indicators.",
            "keywords": ["粉丝", "点赞", "评论", "标题", "内容", "音乐", "爆款", "DCI"],
            "next_action": "Split observable platform metrics from service-path indicators.",
        },
        {
            "slot": "Boundary paragraph",
            "purpose": "State scope limits by library type, platform, time window, and evidence status.",
            "keywords": ["公共图书馆", "高校图书馆", "平台", "比较", "差异", "时间"],
            "next_action": "Add 2024-2026 data before making current-platform claims.",
        },
    ]
    paragraph_traces = []
    for rule in paragraph_rules:
        matched = match_claim_rows(rows, list(rule["keywords"]), limit=8)
        paragraph_traces.append(
            {
                "slot": rule["slot"],
                "purpose": rule["purpose"],
                "linked_claims": claim_brief(matched),
                "source_trace": source_trace(matched),
                "readiness": readiness(matched) if matched else "No linked claim yet",
                "next_action": rule["next_action"],
            }
        )
    return {
        "schema_version": "ResearchWorkflow.WritingTraceability.v1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "project": project_slug,
        "summary": {
            "claim_link_rows": len(rows),
            "unique_claims": len(grouped),
            "page_located_rows": located,
            "page_pending_rows": len(rows) - located,
            "human_ready_rows": human_ready,
        },
        "research_question_traces": question_traces,
        "variable_traces": variable_traces,
        "paragraph_traces": paragraph_traces,
    }


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


def render_md(project_slug: str, project: Path, trace: dict[str, object] | None = None) -> str:
    questions = current_questions(project)
    rows, located, pending = evidence_summary(project)
    trace = trace or traceability_payload(project_slug, project)
    summary = trace["summary"]
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
            "## Claim Evidence Traceability",
            "",
        ]
    )
    lines.extend(
        md_table(
            [
                ["Metric", "Value"],
                ["Claim link rows", str(summary["claim_link_rows"])],
                ["Unique claims", str(summary["unique_claims"])],
                ["Page located rows", str(summary["page_located_rows"])],
                ["Page pending rows", str(summary["page_pending_rows"])],
                ["Human-ready rows", str(summary["human_ready_rows"])],
            ]
        )
    )
    lines.extend(["", "## Research Question Evidence Trace", ""])
    lines.extend(
        md_table(
            [["Slot", "Research question", "Linked claims", "Source trace", "Readiness"]]
            + [
                [
                    str(item["slot"]),
                    str(item["question"]),
                    str(item["linked_claims"]),
                    str(item["source_trace"]),
                    str(item["readiness"]),
                ]
                for item in trace["research_question_traces"]
            ]
        )
    )
    lines.extend(["", "## Variable And Indicator Evidence Trace", ""])
    lines.extend(
        md_table(
            [["Layer", "Candidate indicators", "Linked claims", "Source trace", "Boundary"]]
            + [
                [
                    str(item["layer"]),
                    str(item["candidate_indicators"]),
                    str(item["linked_claims"]),
                    str(item["source_trace"]),
                    str(item["boundary"]),
                ]
                for item in trace["variable_traces"]
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
        ]
    )
    lines.extend(
        md_table(
            [["Paragraph slot", "Purpose", "Linked claims", "Source trace", "Readiness", "Next action"]]
            + [
                [
                    str(item["slot"]),
                    str(item["purpose"]),
                    str(item["linked_claims"]),
                    str(item["source_trace"]),
                    str(item["readiness"]),
                    str(item["next_action"]),
                ]
                for item in trace["paragraph_traces"]
            ]
        )
    )
    lines.extend(
        [
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
    parser.add_argument("--project", default=active_project_slug())
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    out_dir = project / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "writing_panel.md"
    html_path = out_dir / "writing_panel.html"
    trace_path = out_dir / "writing_traceability.json"
    trace = traceability_payload(args.project, project)
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_text = render_md(args.project, project, trace=trace)
    md_path.write_text(md_text + "\n", encoding="utf-8")
    html_path.write_text(render_html(args.project, md_text, html_path, md_path), encoding="utf-8")
    print(f"Wrote manuscript traceability data: {trace_path}")
    print(f"Wrote manuscript panel markdown: {md_path}")
    print(f"Wrote manuscript panel HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
