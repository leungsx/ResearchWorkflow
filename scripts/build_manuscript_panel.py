#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

from rendering.routes import paper_markdown_view_path
from workflow_config import active_project_slug


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
READY_READ_STATUSES = {"human-read", "verified", "claim-linked", "manuscript-cited"}
VERIFICATION_FIELDS = [
    "task_id",
    "priority",
    "verification_status",
    "claim_id",
    "claim_text",
    "citekey",
    "title",
    "source_block_id",
    "page",
    "locator_status",
    "read_status",
    "used_in_manuscript",
    "risk",
    "source_path",
    "reader_display_path",
    "source_map",
    "snippet",
    "next_action",
]


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def href(target: Path, from_file: Path) -> str:
    relative = os.path.relpath(target, from_file.parent).replace(os.sep, "/")
    return quote(relative, safe="/#:.?=&%-_")


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


def locator_rows(project: Path) -> list[dict[str, str]]:
    return csv_rows(project / "literature" / "evidence_locator_table.csv")


def locator_index(project: Path) -> dict[str, dict[str, str]]:
    return {clean(row.get("source_id", "")): row for row in locator_rows(project) if clean(row.get("source_id", ""))}


def truthy(value: str) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return text or "item"


def reader_display_path(source_path: str) -> str:
    if not clean(source_path):
        return ""
    source = Path(source_path)
    if not source.is_absolute():
        source = ROOT / source
    if not source.exists() or source.suffix != ".md":
        return ""
    display = paper_markdown_view_path(source)
    return rel(display) if display.exists() else ""


def verification_status(row: dict[str, str]) -> str:
    page = clean(row.get("page", ""))
    locator = clean(row.get("locator_status", ""))
    read_status = clean(row.get("read_status", ""))
    if not page:
        return "needs_page_locator"
    if locator == "page_located_needs_human_check":
        return "needs_page_check"
    if read_status not in READY_READ_STATUSES:
        return "needs_human_read"
    return "ready_for_manuscript_review"


def verification_priority(row: dict[str, str]) -> int:
    score = 10
    status = verification_status(row)
    if truthy(row.get("used_in_manuscript", "")):
        score += 100
    if status == "needs_page_locator":
        score += 50
    elif status == "needs_page_check":
        score += 40
    elif status == "needs_human_read":
        score += 25
    if "statistical" in clean(row.get("risk", "")).lower():
        score += 15
    if clean(row.get("strength", "")) == "candidate":
        score += 5
    return score


def next_verification_action(status: str) -> str:
    actions = {
        "needs_page_locator": "Open original PDF/Reader and fill exact page or table locator.",
        "needs_page_check": "Check the extracted page/table against the original PDF.",
        "needs_human_read": "Read the source block manually before treating it as manuscript evidence.",
        "ready_for_manuscript_review": "Ready for final manuscript wording and citation audit.",
    }
    return actions.get(status, "Review before use.")


def verification_queue_rows(project: Path) -> list[dict[str, str]]:
    locators = locator_index(project)
    rows: list[dict[str, str]] = []
    for row in claim_links(project):
        source_id = clean(row.get("source_block_id", ""))
        locator = locators.get(source_id, {})
        status = verification_status(row)
        rows.append(
            {
                "task_id": f"verify-{slug(clean(row.get('claim_id', '')))}-{slug(source_id)}",
                "priority": str(verification_priority(row)),
                "verification_status": status,
                "claim_id": clean(row.get("claim_id", "")),
                "claim_text": clean(row.get("claim_text", "")),
                "citekey": clean(row.get("citekey", "")),
                "title": clean(locator.get("title", "")),
                "source_block_id": source_id,
                "page": clean(row.get("page", "")),
                "locator_status": clean(row.get("locator_status", "")),
                "read_status": clean(row.get("read_status", "")),
                "used_in_manuscript": clean(row.get("used_in_manuscript", "")).lower() or "false",
                "risk": clean(row.get("risk", "")),
                "source_path": clean(row.get("source_path", "")),
                "reader_display_path": reader_display_path(clean(row.get("source_path", ""))),
                "source_map": clean(locator.get("source_map", "")),
                "snippet": clean(locator.get("snippet", "")),
                "next_action": next_verification_action(status),
            }
        )
    rows.sort(key=lambda item: (-int(item["priority"]), item["claim_id"], item["citekey"], item["source_block_id"]))
    return rows


def verification_summary(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "total_items": len(rows),
        "needs_page_locator": sum(1 for row in rows if row["verification_status"] == "needs_page_locator"),
        "needs_page_check": sum(1 for row in rows if row["verification_status"] == "needs_page_check"),
        "needs_human_read": sum(1 for row in rows if row["verification_status"] == "needs_human_read"),
        "ready_for_manuscript_review": sum(1 for row in rows if row["verification_status"] == "ready_for_manuscript_review"),
    }


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
    located = sum(1 for row in rows if clean(row.get("page", "")))
    human_ready = sum(1 for row in rows if clean(row.get("read_status", "")) in READY_READ_STATUSES)
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


def traceability_payload(project_slug: str, project: Path, queue_rows: list[dict[str, str]] | None = None) -> dict[str, object]:
    rows = claim_links(project)
    grouped = group_claims(rows)
    located = sum(1 for row in rows if clean(row.get("page", "")))
    human_ready = sum(1 for row in rows if clean(row.get("read_status", "")) in READY_READ_STATUSES)
    queue_rows = queue_rows if queue_rows is not None else verification_queue_rows(project)
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
        "verification_queue_summary": verification_summary(queue_rows),
        "top_verification_tasks": [
            {key: item[key] for key in ["task_id", "priority", "verification_status", "claim_id", "citekey", "source_block_id", "page", "read_status", "next_action"]}
            for item in queue_rows[:8]
        ],
        "research_question_traces": question_traces,
        "variable_traces": variable_traces,
        "paragraph_traces": paragraph_traces,
    }


def write_verification_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VERIFICATION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_verification_json(path: Path, project_slug: str, rows: list[dict[str, str]]) -> None:
    payload = {
        "schema_version": "ResearchWorkflow.PageVerificationQueue.v1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "project": project_slug,
        "summary": verification_summary(rows),
        "items": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_verification_html(path: Path, project_slug: str, rows: list[dict[str, str]], csv_path: Path, json_path: Path) -> None:
    summary = verification_summary(rows)

    def source_cell(row: dict[str, str]) -> str:
        label = html.escape(row["source_block_id"])
        display = clean(row.get("reader_display_path", ""))
        source_text = html.escape(row.get("source_path", ""))
        if display:
            link = href(ROOT / display, path)
            return f'<a href="{link}"><code>{label}</code></a><br><span>{source_text}</span>'
        return f"<code>{label}</code><br><span>{source_text}</span>"

    table_rows = "\n".join(
        f"""
        <tr>
          <td><code>{html.escape(row['claim_id'])}</code><br>{html.escape(row['claim_text'])}</td>
          <td>{html.escape(row['title'] or row['citekey'])}<br><code>{html.escape(row['citekey'])}</code></td>
          <td>{source_cell(row)}</td>
          <td>{html.escape(row['page'] or '待补')}</td>
          <td><code>{html.escape(row['verification_status'])}</code><br><span>{html.escape(row['read_status'])}</span></td>
          <td>{html.escape(row['next_action'])}</td>
          <td>{html.escape(row['snippet'])}</td>
        </tr>
        """
        for row in rows[:120]
    )
    path.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>页码级证据核验队列 - {html.escape(project_slug)}</title>
  <style>
    :root {{ --ink:#1e293b; --muted:#64748b; --line:#dbe4ee; --paper:#fff; --soft:#f8fafc; --blue:#2563eb; --shadow:0 10px 28px rgba(15,23,42,.06); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:#f8fafc; line-height:1.62; }}
    header {{ background:#fff; border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:1280px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:0 0 12px; font-size:21px; }}
    a {{ color:var(--blue); text-decoration:none; }}
    .sub, span {{ color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(12,1fr); gap:14px; }}
    .metric, .panel {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:var(--shadow); }}
    .metric {{ grid-column:span 3; }}
    .metric b {{ display:block; font-size:28px; }}
    .panel {{ grid-column:1/-1; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th, td {{ text-align:left; vertical-align:top; border-bottom:1px solid var(--line); padding:10px 8px; }}
    th {{ color:var(--muted); background:#fbfdff; }}
    code {{ background:#eef3f8; border:1px solid #d8e2ec; border-radius:5px; padding:1px 4px; }}
    @media (max-width:900px) {{ .metric {{ grid-column:1/-1; }} table {{ display:block; overflow-x:auto; }} h1 {{ font-size:28px; }} }}
  </style>
</head>
<body>
  <header><div class="wrap">
    <h1>页码级证据核验队列</h1>
    <p class="sub">{html.escape(project_slug)} · Generated {html.escape(dt.datetime.now().isoformat(timespec='seconds'))}</p>
    <p><a href="../../../study_dashboard.html">返回学习仪表盘</a> · <a href="../manuscript/writing_panel.html">论文写作面板</a> · <a href="{html.escape(csv_path.name)}">CSV</a> · <a href="{html.escape(json_path.name)}">JSON</a></p>
  </div></header>
  <main class="wrap">
    <section class="grid">
      <div class="metric"><b>{summary['total_items']}</b><span>核验任务</span></div>
      <div class="metric"><b>{summary['needs_page_locator']}</b><span>待补页码</span></div>
      <div class="metric"><b>{summary['needs_page_check']}</b><span>待人工核页</span></div>
      <div class="metric"><b>{summary['ready_for_manuscript_review']}</b><span>可进入写作审查</span></div>
      <section class="panel">
        <h2>Claim -> Source Block -> Page -> Read Status</h2>
        <table>
          <thead><tr><th>Claim</th><th>文献</th><th>Source block</th><th>页码</th><th>状态</th><th>下一步</th><th>证据片段</th></tr></thead>
          <tbody>{table_rows or '<tr><td colspan="7">暂无待核验证据。</td></tr>'}</tbody>
        </table>
      </section>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


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
    queue_summary = trace["verification_queue_summary"]
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
    lines.extend(["", "## Page Verification Queue", ""])
    lines.extend(
        md_table(
            [
                ["Metric", "Value"],
                ["Total verification tasks", str(queue_summary["total_items"])],
                ["Need page locator", str(queue_summary["needs_page_locator"])],
                ["Need page check", str(queue_summary["needs_page_check"])],
                ["Need human read", str(queue_summary["needs_human_read"])],
                ["Ready for manuscript review", str(queue_summary["ready_for_manuscript_review"])],
            ]
        )
    )
    lines.extend(["", "## Top Verification Tasks", ""])
    lines.extend(
        md_table(
            [["Task", "Claim", "Source block", "Page", "Read status", "Next action"]]
            + [
                [
                    str(item["task_id"]),
                    str(item["claim_id"]),
                    str(item["source_block_id"]),
                    str(item["page"] or "待补"),
                    str(item["read_status"]),
                    str(item["next_action"]),
                ]
                for item in trace["top_verification_tasks"]
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
    <p><a href="../../../study_dashboard.html">返回学习仪表盘</a> · <a href="../evidence/page_verification_queue.html">页码核验队列</a></p>
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
    queue_rows = verification_queue_rows(project)
    queue_csv = project / "evidence" / "page_verification_queue.csv"
    queue_json = project / "evidence" / "page_verification_queue.json"
    queue_html = project / "evidence" / "page_verification_queue.html"
    write_verification_csv(queue_csv, queue_rows)
    write_verification_json(queue_json, args.project, queue_rows)
    write_verification_html(queue_html, args.project, queue_rows, queue_csv, queue_json)
    trace = traceability_payload(args.project, project, queue_rows=queue_rows)
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_text = render_md(args.project, project, trace=trace)
    md_path.write_text(md_text + "\n", encoding="utf-8")
    html_path.write_text(render_html(args.project, md_text, html_path, md_path), encoding="utf-8")
    print(f"Wrote page verification queue CSV: {queue_csv}")
    print(f"Wrote page verification queue JSON: {queue_json}")
    print(f"Wrote page verification queue HTML: {queue_html}")
    print(f"Wrote manuscript traceability data: {trace_path}")
    print(f"Wrote manuscript panel markdown: {md_path}")
    print(f"Wrote manuscript panel HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
