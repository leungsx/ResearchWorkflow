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

from rendering.io import write_json_if_changed, write_text_if_changed
from rendering.routes import paper_markdown_view_path
from rendering.ui import render_shell
from workflow_config import active_project_slug


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
READY_READ_STATUSES = {"human-read", "verified"}
CRITICAL_USAGE_STATUSES = {"claim-linked", "manuscript-cited", "submission-evidence"}
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
    "evidence_usage_status",
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


QUESTION_TRANSLATIONS = {
    "How can visible platform engagement from library short videos be translated into observable service value in digital reading promotion?": "可见的平台互动数据如何转化为数字阅读推广中可观察的图书馆服务价值？",
    "Which content cues and service-design mechanisms move users from sense/interest into interaction, connection, and service action?": "哪些内容线索和服务设计机制能推动用户从感知、兴趣走向互动、连接和服务行动？",
    "How should service-value indicators vary across public libraries, university libraries, research-oriented libraries, and short-video platforms?": "公共图书馆、高校图书馆、科研型图书馆及不同短视频平台的服务价值指标应如何区分？",
}
READ_STATUS_LABELS = {
    "metadata-only": "仅元数据",
    "skimmed": "已扫读",
    "source-grounded": "有来源笔记",
    "human-read": "已人工精读",
    "verified": "已核验",
}
USAGE_STATUS_LABELS = {
    "candidate": "候选证据",
    "claim-linked": "已连到主张",
    "manuscript-cited": "已进入正文",
    "submission-evidence": "投稿证据",
}
VERIFICATION_STATUS_LABELS = {
    "needs_page_locator": "待补页码",
    "needs_page_check": "待人工核页",
    "needs_human_read": "待读原文确认",
    "ready_for_manuscript_review": "可进入写作审查",
}


def zh_question(value: str) -> str:
    text = clean(value)
    prefixes = [
        ("Main question:", "主问题："),
        ("Sub-question 1:", "子问题1："),
        ("Sub-question 2:", "子问题2："),
        ("Research question:", "研究问题："),
    ]
    for prefix, zh_prefix in prefixes:
        if text.startswith(prefix):
            body = clean(text[len(prefix) :])
            return zh_prefix + QUESTION_TRANSLATIONS.get(body, body)
    return QUESTION_TRANSLATIONS.get(text, text)


def zh_read_status(value: str) -> str:
    text = clean(value)
    return READ_STATUS_LABELS.get(text, text or "未知")


def zh_usage_status(value: str) -> str:
    text = clean(value)
    return USAGE_STATUS_LABELS.get(text, text or "未标注")


def zh_verification_status(value: str) -> str:
    text = clean(value)
    return VERIFICATION_STATUS_LABELS.get(text, text or "待核验")


def verification_status_class(value: str) -> str:
    text = clean(value)
    if text == "ready_for_manuscript_review":
        return "pass"
    if text == "needs_human_read":
        return "info"
    return "warn"


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
            questions.append(zh_question(line.lstrip("- ")))
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


def evidence_usage_status(row: dict[str, str]) -> str:
    explicit = clean(row.get("evidence_usage_status", ""))
    if explicit:
        return explicit
    if truthy(row.get("used_in_manuscript", "")):
        return "manuscript-cited"
    return "candidate"


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
    usage = evidence_usage_status(row)
    if usage in CRITICAL_USAGE_STATUSES or truthy(row.get("used_in_manuscript", "")):
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
        "needs_page_locator": "打开原文 PDF 或阅读包，补入准确页码或表格位置。",
        "needs_page_check": "对照原文核查已抽取的页码或表格位置。",
        "needs_human_read": "先人工阅读来源片段，再把它作为正文证据。",
        "ready_for_manuscript_review": "可进入正文措辞和引用审计。",
    }
    return actions.get(status, "使用前再核验一次。")


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
                "evidence_usage_status": evidence_usage_status(row),
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
    page = clean(row.get("page", "")) or "页码待补"
    return f"{clean(row.get('source_block_id', ''))} / {page} / {zh_read_status(row.get('read_status', ''))}"


def readiness(rows: list[dict[str, str]]) -> str:
    located = sum(1 for row in rows if clean(row.get("page", "")))
    human_ready = sum(1 for row in rows if clean(row.get("read_status", "")) in READY_READ_STATUSES)
    return f"{human_ready}/{len(rows)} 已人工确认；{located}/{len(rows)} 已定位页码"


def claim_brief(rows: list[dict[str, str]], limit: int = 4) -> str:
    if not rows:
        return "暂无关联主张"
    grouped = group_claims(rows)
    labels = []
    for claim_id, claim_rows in list(grouped.items())[:limit]:
        labels.append(f"{claim_id} ({readiness(claim_rows)})")
    if len(grouped) > limit:
        labels.append(f"另有 {len(grouped) - limit} 项")
    return "; ".join(labels)


def source_trace(rows: list[dict[str, str]], limit: int = 3) -> str:
    traces = [row_trace(row) for row in rows[:limit]]
    if len(rows) > limit:
        traces.append(f"另有 {len(rows) - limit} 条")
    return "；".join(traces) if traces else "暂无来源线索"


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
        ("主问题", ["平台", "服务价值", "阅读推广", "传播力", "SICAS", "AARRR", "数字阅读"]),
        ("子问题1", ["标题", "内容", "音乐", "互动", "行动", "SICAS", "Hook", "机制"]),
        ("子问题2", ["公共图书馆", "高校图书馆", "平台", "差异", "馆型", "比较", "AARRR"]),
    ]
    question_traces = []
    for index, question in enumerate(questions[:3]):
        label, keywords = question_rules[index] if index < len(question_rules) else (f"问题{index + 1}", [])
        matched = match_claim_rows(rows, keywords or [question], limit=8)
        question_traces.append(
            {
                "slot": label,
                "question": question,
                "linked_claims": claim_brief(matched),
                "source_trace": source_trace(matched),
                "readiness": readiness(matched) if matched else "暂无关联主张",
            }
        )

    variable_rules = [
        {
            "layer": "平台互动层",
            "indicators": "粉丝量、发布量、点赞/评论/转发、爆款指数、DCI/传播力指数、标题/音乐/内容形式",
            "keywords": ["粉丝", "发布", "点赞", "评论", "转发", "爆款", "DCI", "传播力", "标题", "音乐", "内容"],
            "boundary": "可支持可见度和互动判断，但不能单独证明服务价值。",
        },
        {
            "layer": "服务触点层",
            "indicators": "资源入口、活动入口、咨询/连接路径、线上线下转换、服务信息清晰度",
            "keywords": ["服务", "触达", "资源", "活动", "咨询", "线上线下", "渠道", "互动营销", "数字阅读"],
            "boundary": "进入正文前需要可观察的服务路径或图书馆服务结果支撑。",
        },
        {
            "layer": "阅读推广成效层",
            "indicators": "阅读参与、资源访问、活动报名、读者反馈、知识传播效果、分享回流",
            "keywords": ["阅读", "服务价值", "行动", "分享", "资源", "活动", "知识传播", "SICAS"],
            "boundary": "当前文献可支持框架设计，成效测量仍需要更强数据。",
        },
        {
            "layer": "边界与比较层",
            "indicators": "馆型、平台类型、时间窗口、账号规模、公共馆/高校馆/科研型图书馆差异",
            "keywords": ["公共图书馆", "高校图书馆", "馆型", "平台", "差异", "比较", "账号"],
            "boundary": "不能把单一平台或单一时间窗口的结论外推到所有图书馆情境。",
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
            "slot": "文献缺口段",
            "purpose": "说明为什么需要区分平台可见度和图书馆服务价值。",
            "keywords": ["服务价值", "传播力", "数字阅读", "平台", "互动"],
            "next_action": "补齐页码或表格定位后，再写成正式综述判断。",
        },
        {
            "slot": "框架段",
            "purpose": "交代“平台互动-服务触点-阅读推广成效”的概念链。",
            "keywords": ["SICAS", "AARRR", "服务", "阅读推广", "行动", "分享"],
            "next_action": "在新数据或页码级证据确认前，避免写成因果判断。",
        },
        {
            "slot": "变量段",
            "purpose": "把既有研究转成可观察变量和候选指标。",
            "keywords": ["粉丝", "点赞", "评论", "标题", "内容", "音乐", "爆款", "DCI"],
            "next_action": "把平台互动指标和服务路径指标分开表述。",
        },
        {
            "slot": "边界段",
            "purpose": "说明馆型、平台、时间窗口和证据状态的外推边界。",
            "keywords": ["公共图书馆", "高校图书馆", "平台", "比较", "差异", "时间"],
            "next_action": "补充 2024-2026 年数据后，再写当前平台判断。",
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
                "readiness": readiness(matched) if matched else "暂无关联主张",
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
            {key: item[key] for key in ["task_id", "priority", "verification_status", "claim_id", "citekey", "source_block_id", "page", "read_status", "evidence_usage_status", "next_action"]}
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
    write_json_if_changed(path, payload)


def write_verification_html(path: Path, project_slug: str, rows: list[dict[str, str]], csv_path: Path, json_path: Path) -> None:
    summary = verification_summary(rows)
    rebuild_command = f"make manuscript-panel PROJECT={project_slug}"
    gate_command = f"make evidence-gate PROJECT={project_slug}"
    sync_command = f"make claim-evidence-sync PROJECT={project_slug}"

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
          <td><span class="status-pill {verification_status_class(row['verification_status'])}">{html.escape(zh_verification_status(row['verification_status']))}</span><br><span>{html.escape(zh_read_status(row['read_status']))} / {html.escape(zh_usage_status(row['evidence_usage_status']))}</span></td>
          <td>{html.escape(row['next_action'])}</td>
          <td>{html.escape(row['snippet'])}</td>
        </tr>
        """
        for row in rows[:120]
    )
    body = f"""
    <div class="toolbar">
      <a class="button primary" href="{html.escape(csv_path.name)}">CSV 数据</a>
      <a class="button" href="{html.escape(json_path.name)}">JSON 数据</a>
      <button type="button" class="button" data-copy="{html.escape(rebuild_command)}" data-label="复制刷新命令">复制刷新命令</button>
      <button type="button" class="button" data-copy="{html.escape(gate_command)}" data-label="复制门禁命令">复制门禁命令</button>
      <button type="button" class="button" data-copy="{html.escape(sync_command)}" data-label="复制同步命令">复制同步命令</button>
    </div>
    <div class="copy-feedback" aria-live="polite"></div>
    <section class="grid">
      <div class="metric"><b>{summary['total_items']}</b><span>核验任务</span></div>
      <div class="metric"><b>{summary['needs_page_locator']}</b><span>待补页码</span></div>
      <div class="metric"><b>{summary['needs_page_check']}</b><span>待人工核页</span></div>
      <div class="metric"><b>{summary['ready_for_manuscript_review']}</b><span>可进入写作审查</span></div>
      <section class="panel wide table-panel">
        <h2>主张-来源片段-页码-阅读状态链</h2>
        <div class="table-wrap">
        <table class="data-table verification-table">
          <thead><tr><th>主张</th><th>文献</th><th>来源片段</th><th>页码</th><th>核验状态</th><th>下一步</th><th>证据摘录</th></tr></thead>
          <tbody>{table_rows or '<tr><td colspan="7">暂无待核验证据。</td></tr>'}</tbody>
        </table>
        </div>
      </section>
    </section>
"""
    html_text = render_shell(
        title="核页码",
        subtitle="补全主张、来源片段、页码和阅读状态，优先处理已经进入写作链的证据。",
        current="核页码",
        body=body,
        output=path,
        module="证据",
        meta=f"{html.escape(project_slug)} · 主张-来源片段-页码-阅读状态",
        footer="由 scripts/build_manuscript_panel.py 自动生成。",
    )
    write_text_if_changed(path, html_text)


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
        "# 写论文",
        "",
        "由 `scripts/build_manuscript_panel.py` 自动生成。",
        f"当前项目：`{project_slug}`",
        "",
        "## 当前论文方向",
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
            "## 工作概念链",
            "",
            "`平台互动 -> 服务触点 -> 阅读推广成效`",
            "",
            "- SICAS 用来解释用户从感知、兴趣到行动、分享的路径。",
            "- AARRR 用来组织生命周期指标，但必须转译成图书馆服务结果。",
            "- 传播力指标描述可见度和互动强度，不能单独证明服务价值。",
            "",
            "## 变量与指标草案",
            "",
        ]
    )
    lines.extend(
        md_table(
            [
                ["层级", "候选指标", "当前证据", "写作前风险"],
                ["平台互动层", "粉丝量、发布量、点赞/评论/转发、爆款指数、DCI/传播力指数", "传播力评价、DCI、爆款指数相关阅读包", "容易把平台热度误写成服务价值"],
                ["服务触点层", "资源入口、活动入口、咨询/连接路径、线上线下转换、服务信息清晰度", "SICAS、AARRR、数字阅读推广与营销策略文献", "服务触达仍需可观察指标"],
                ["阅读成效层", "阅读参与、资源访问、活动报名、读者反馈、知识传播效果", "目前多为框架启发，直接证据不足", "需要后续数据或更强文献补证"],
                ["边界层", "馆型差异、平台差异、时间窗口、账号规模", "公共馆/高校馆比较、平台适配文献", "不能用单平台结论外推所有馆型"],
            ]
        )
    )
    lines.extend(
        [
            "",
            "## 主张证据可追溯性",
            "",
        ]
    )
    lines.extend(
        md_table(
            [
                ["指标", "数值"],
                ["主张-证据链接行", str(summary["claim_link_rows"])],
                ["唯一主张数", str(summary["unique_claims"])],
                ["已定位页码行", str(summary["page_located_rows"])],
                ["待补页码行", str(summary["page_pending_rows"])],
                ["已人工确认行", str(summary["human_ready_rows"])],
            ]
        )
    )
    lines.extend(["", "## 研究问题证据追踪", ""])
    lines.extend(
        md_table(
            [["位置", "研究问题", "关联主张", "来源线索", "证据成熟度"]]
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
    lines.extend(["", "## 变量与指标证据追踪", ""])
    lines.extend(
        md_table(
            [["层级", "候选指标", "关联主张", "来源线索", "边界"]]
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
            "## 证据成熟度",
            "",
            f"- 定位行数：{rows}",
            f"- 已定位页码：{located}",
            f"- 页码待补：{pending}",
            "",
            "## 段落队列",
            "",
        ]
    )
    lines.extend(
        md_table(
            [["段落位置", "写作目的", "关联主张", "来源线索", "证据成熟度", "下一步"]]
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
    lines.extend(["", "## 页码核验队列", ""])
    lines.extend(
        md_table(
            [
                ["指标", "数值"],
                ["核验任务总数", str(queue_summary["total_items"])],
                ["待补页码", str(queue_summary["needs_page_locator"])],
                ["待人工核页", str(queue_summary["needs_page_check"])],
                ["待读原文确认", str(queue_summary["needs_human_read"])],
                ["可进入写作审查", str(queue_summary["ready_for_manuscript_review"])],
            ]
        )
    )
    lines.extend(["", "## 优先核验任务", ""])
    lines.extend(
        md_table(
            [["任务", "主张", "来源片段", "页码", "阅读状态", "使用状态", "下一步"]]
            + [
                [
                    str(item["task_id"]),
                    str(item["claim_id"]),
                    str(item["source_block_id"]),
                    str(item["page"] or "待补"),
                    zh_read_status(str(item["read_status"])),
                    zh_usage_status(str(item["evidence_usage_status"])),
                    str(item["next_action"]),
                ]
                for item in trace["top_verification_tasks"]
            ]
        )
    )
    lines.extend(
        [
            "",
            "## 下一步写作动作",
            "",
            "- 先核验当前标为“页码待补”的证据行，补齐页码或表格定位。",
            "- 只有真实读过原文后，才把最强的传播力/服务价值论文从“已扫读”升级为“已人工精读”。",
            "- 写引言和综述前，先在 `07_claim_evidence_map.md` 中沉淀 3-5 条可写主张。",
            "- 仅元数据论文不要进入正文主张，除非已经有阅读包或全文笔记。",
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
                body_parts.append("</tbody></table></div>")
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
                body_parts.append(f'<div class="table-wrap"><table class="data-table"><thead><tr>{header}</tr></thead><tbody>')
                in_table = True
            else:
                body_parts.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        elif clean(line):
            body_parts.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body_parts.append("</tbody></table></div>")
    rebuild_command = f"make manuscript-panel PROJECT={project_slug}"
    gate_command = f"make evidence-gate PROJECT={project_slug}"
    sync_command = f"make claim-evidence-sync PROJECT={project_slug}"
    body = f"""
    <div class="toolbar">
      <a class="button primary" href="../evidence/page_verification_queue.html">核页码</a>
      <button type="button" class="button" data-copy="{html.escape(rebuild_command)}" data-label="复制刷新命令">复制刷新命令</button>
      <button type="button" class="button" data-copy="{html.escape(gate_command)}" data-label="复制门禁命令">复制门禁命令</button>
      <button type="button" class="button" data-copy="{html.escape(sync_command)}" data-label="复制同步命令">复制同步命令</button>
    </div>
    <div class="copy-feedback" aria-live="polite"></div>
    <article class="panel wide writing-panel">
    {''.join(body_parts)}
    </article>
"""
    return render_shell(
        title="写论文",
        subtitle="把已读文献转成研究问题、变量指标、证据链和可写段落。",
        current="写论文",
        body=body,
        output=html_path,
        module="写作",
        meta=f"{html.escape(project_slug)} · 研究问题、变量指标、证据链和段落队列",
        footer="由 scripts/build_manuscript_panel.py 自动生成。",
    )


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
    write_json_if_changed(trace_path, trace)
    md_text = render_md(args.project, project, trace=trace)
    write_text_if_changed(md_path, md_text + "\n")
    write_text_if_changed(html_path, render_html(args.project, md_text, html_path, md_path))
    print(f"Wrote page verification queue CSV: {queue_csv}")
    print(f"Wrote page verification queue JSON: {queue_json}")
    print(f"Wrote page verification queue HTML: {queue_html}")
    print(f"Wrote manuscript traceability data: {trace_path}")
    print(f"Wrote manuscript panel markdown: {md_path}")
    print(f"Wrote manuscript panel HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
