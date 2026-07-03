#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
from io import StringIO
from pathlib import Path
from typing import Any

from rendering.io import write_json_if_changed, write_text_if_changed, write_text_preserving_generated_at
from rendering.ui import render_advanced_actions, render_guidance, render_shell
from workflow_config import active_project_slug


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"
FULLTEXT_SUFFIXES = {".pdf", ".caj", ".kdh", ".nh"}

GAP_TERMS = {
    "传播力评价": ["传播力", "传播效果", "互动效果", "评价", "指标", "指数", "DCI", "爆款"],
    "服务价值指标": ["服务价值", "阅读服务", "阅读推广", "服务", "转化", "用户体验", "公众平台"],
    "机制解释": ["机制", "模型", "路径", "影响因素", "组态", "文本分析", "SICAS", "上瘾模型"],
}

EXTERNAL_TERMS = ["非遗", "政务", "共青团", "档案", "皮影"]

ACTION_LABELS = {
    "candidate_for_deep_read": "候选精读",
    "build_reader": "生成 Reader",
    "intake_to_stable_pdf": "入库为稳定 PDF",
    "add_to_matrix_or_mark_external": "补入矩阵或标外部",
    "manual_check_topic_fit": "人工判断主题",
    "already_read_keep_as_backup": "已读，保留备份",
    "already_skimmed_keep_as_backup": "已略读，保留备份",
    "duplicate_keep_one_then_archive": "重复件，保留一份",
    "external_comparison_or_ignore": "外部对照或忽略",
}

READ_STATUS_LABELS = {
    "metadata-only": "仅有元数据",
    "unread": "未读",
    "skimmed": "已略读",
    "human-read": "已精读",
    "verified": "已核验",
    "unmatched": "未匹配",
}

EVIDENCE_VALUE_LABELS = {
    "high": "高",
    "medium-high": "中高",
    "medium": "中",
    "review": "待复核",
    "unknown": "待判断",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    item = Path(path)
    try:
        return item.relative_to(ROOT).as_posix()
    except ValueError:
        return str(item)


def normalize(value: str) -> str:
    return re.sub(r"[\s_《》<>“”\"'，,。．.：:；;、（）()\[\]【】\-—]+", "", value or "").lower()


def duplicate_key(value: str) -> str:
    stem = Path(value).stem
    stem = re.sub(r"\s*[\(（]\d+[\)）]\s*$", "", stem)
    return normalize(stem)


def has_copy_suffix(value: str) -> bool:
    return bool(re.search(r"[\(（]\d+[\)）]\s*$", Path(value).stem))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_path(value: str) -> Path | None:
    value = clean(value)
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def project_rows(project: str) -> list[dict[str, str]]:
    return [row for row in read_csv(MATRIX) if project in row.get("project_tags", "")]


def incoming_files(project: str, explicit: Path | None) -> list[Path]:
    base = explicit or (ROOT / "library" / "pdfs" / project / "incoming")
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in FULLTEXT_SUFFIXES)


def reader_exists(project: str, citekey: str) -> bool:
    return (PROJECTS / project / "literature" / "readers" / citekey / "paper.md").exists()


def stable_fulltext_exists(row: dict[str, str]) -> bool:
    path = resolve_path(row.get("pdf_path", ""))
    return bool(path and path.exists())


def match_row(path: Path, rows: list[dict[str, str]]) -> dict[str, str] | None:
    name = path.stem
    name_key = normalize(name)
    for row in rows:
        citekey = clean(row.get("citekey"))
        if citekey and citekey in name:
            return row
    title_matches: list[dict[str, str]] = []
    for row in rows:
        title_key = normalize(row.get("title", ""))
        if title_key and (title_key in name_key or name_key in title_key):
            title_matches.append(row)
    if len(title_matches) == 1:
        return title_matches[0]
    for row in rows:
        title_key = normalize(row.get("title", ""))
        if title_key and len(title_key) >= 14 and title_key[:14] in name_key:
            return row
    return None


def gap_tags(text: str) -> list[str]:
    tags: list[str] = []
    for gap, terms in GAP_TERMS.items():
        if any(term and term in text for term in terms):
            tags.append(gap)
    return tags


def next_action(path: Path, row: dict[str, str] | None, tags: list[str], duplicate_copy: bool, project: str) -> str:
    text = path.name
    if duplicate_copy:
        return "duplicate_keep_one_then_archive"
    if any(term in text for term in EXTERNAL_TERMS) and not row:
        return "external_comparison_or_ignore"
    if not row:
        return "add_to_matrix_or_mark_external" if tags else "manual_check_topic_fit"
    status = clean(row.get("read_status"))
    citekey = clean(row.get("citekey"))
    has_pdf = stable_fulltext_exists(row)
    has_reader = reader_exists(project, citekey)
    if status in {"human-read", "verified"}:
        return "already_read_keep_as_backup"
    if status == "skimmed" and has_reader:
        return "already_skimmed_keep_as_backup"
    if not has_pdf:
        return "intake_to_stable_pdf"
    if not has_reader:
        return "build_reader"
    return "candidate_for_deep_read"


def evidence_value(row: dict[str, str] | None, tags: list[str]) -> str:
    if not row:
        return "medium" if tags else "unknown"
    status = clean(row.get("read_status"))
    if "服务价值指标" in tags:
        return "high"
    if "传播力评价" in tags or "机制解释" in tags:
        return "medium-high"
    if status in {"metadata-only", "", "unread"}:
        return "medium"
    return "review"


def display_label(value: str, labels: dict[str, str]) -> str:
    return labels.get(value, value or "待判断")


def evidence_status_class(value: str) -> str:
    if value in {"high", "medium-high"}:
        return "pass"
    if value in {"unknown", "review"}:
        return "warn"
    return "info"


def build_rows(project: str, explicit_incoming: Path | None) -> list[dict[str, str]]:
    rows = project_rows(project)
    files = incoming_files(project, explicit_incoming)
    normalized_counts: dict[str, int] = {}
    for path in files:
        key = duplicate_key(path.stem)
        normalized_counts[key] = normalized_counts.get(key, 0) + 1

    result: list[dict[str, str]] = []
    for path in files:
        key = duplicate_key(path.stem)
        row = match_row(path, rows)
        text = f"{path.name} {row.get('title', '') if row else ''} {row.get('core_findings', '') if row else ''}"
        tags = gap_tags(text)
        citekey = clean(row.get("citekey")) if row else ""
        has_reader = reader_exists(project, citekey) if citekey else False
        has_pdf = stable_fulltext_exists(row) if row else False
        result.append(
            {
                "file_path": rel(path),
                "file_name": path.name,
                "matched_citekey": citekey,
                "matched_title": clean(row.get("title")) if row else "",
                "read_status": clean(row.get("read_status")) if row else "unmatched",
                "has_pdf": "yes" if has_pdf else "no",
                "has_reader": "yes" if has_reader else "no",
                "project_gap": "；".join(tags) if tags else "待判断",
                "evidence_value": evidence_value(row, tags),
                "duplicate_group_size": str(normalized_counts.get(key, 1)),
                "next_action": next_action(
                    path,
                    row,
                    tags,
                    normalized_counts.get(key, 1) > 1 and has_copy_suffix(path.stem),
                    project,
                ),
            }
        )
    action_rank = {
        "candidate_for_deep_read": 0,
        "build_reader": 1,
        "intake_to_stable_pdf": 2,
        "add_to_matrix_or_mark_external": 3,
        "manual_check_topic_fit": 4,
    }
    return sorted(result, key=lambda row: (action_rank.get(row["next_action"], 9), row["evidence_value"], row["file_name"]))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "file_path",
        "file_name",
        "matched_citekey",
        "matched_title",
        "read_status",
        "has_pdf",
        "has_reader",
        "project_gap",
        "evidence_value",
        "duplicate_group_size",
        "next_action",
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_text_if_changed(path, buffer.getvalue())


def write_json(path: Path, rows: list[dict[str, str]]) -> None:
    payload = {
        "schema_version": "ResearchWorkflow.IncomingTriage.v1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "item_count": len(rows),
        "items": rows,
    }
    write_json_if_changed(path, payload)


def write_md(path: Path, project: str, rows: list[dict[str, str]], csv_path: Path, html_path: Path) -> None:
    lines = [
        f"# Incoming PDF Triage - {project}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"CSV: `{rel(csv_path)}`",
        f"HTML: `{rel(html_path)}`",
        "",
        "## Rule",
        "",
        "- This report only scans and recommends actions; it does not move or delete user files.",
        "- `candidate_for_deep_read` should be considered before already skimmed or external comparison files.",
        "- Duplicates are kept in incoming until the user or an intake command explicitly handles them.",
        "",
        "## Items",
        "",
        "| File | Citekey | Status | Gap | Value | Action |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["file_name"].replace("|", "/"),
                    f"`{row['matched_citekey']}`" if row["matched_citekey"] else "unmatched",
                    row["read_status"],
                    row["project_gap"].replace("|", "/"),
                    row["evidence_value"],
                    f"`{row['next_action']}`",
                ]
            )
            + " |"
        )
    write_text_preserving_generated_at(path, "\n".join(lines) + "\n")


def write_html(path: Path, project: str, rows: list[dict[str, str]], csv_path: Path, json_path: Path, md_path: Path) -> None:
    action_counts: dict[str, int] = {}
    for row in rows:
        action_counts[row["next_action"]] = action_counts.get(row["next_action"], 0) + 1
    cards = "".join(
        f"""<div class="metric">
          <b>{count}</b>
          <span>{html.escape(display_label(action, ACTION_LABELS))}</span>
        </div>"""
        for action, count in sorted(action_counts.items(), key=lambda item: item[0])
    )
    table_rows = "\n".join(
        f"""
        <tr>
          <td><strong>{html.escape(row['file_name'])}</strong><br><span class="source-path table-muted">{html.escape(row['file_path'])}</span></td>
          <td><div class="text-clamp two">{html.escape(row['matched_title'] or '未匹配')}</div><span class="code-badge">{html.escape(row['matched_citekey'] or '未匹配')}</span></td>
          <td><span class="status-pill info">{html.escape(display_label(row['read_status'], READ_STATUS_LABELS))}</span></td>
          <td><div class="text-clamp two">{html.escape(row['project_gap'])}</div></td>
          <td><span class="status-pill {evidence_status_class(row['evidence_value'])}">{html.escape(display_label(row['evidence_value'], EVIDENCE_VALUE_LABELS))}</span></td>
          <td><span class="status-pill">{html.escape(display_label(row['next_action'], ACTION_LABELS))}</span></td>
        </tr>
        """.strip()
        for row in rows
    )
    body = f"""
    {render_guidance(
        purpose="把 incoming 文件夹里的 PDF/CAJ 先分成可入库、可建 Reader、重复件和外部对照，避免直接混入正式文献矩阵。",
        first="优先处理“入库为稳定 PDF”和“生成 Reader”的高证据价值文献；重复件先保留一份，不自动删除。",
        after="入库或生成 Reader 后回到今日精读，选择下一篇能补项目缺口的论文。",
        output=path,
        command=f"make incoming-triage PROJECT={project}",
        action_label="打开今日精读",
        action_target=ROOT / "paper_reading" / "today.html",
    )}
    {render_advanced_actions(
        output=path,
        links=[("CSV 数据", csv_path), ("JSON 数据", json_path)],
    )}
    <section class="summary-grid" aria-label="PDF分拣摘要">{cards or '<div class="metric"><b>0</b><span>incoming 文件</span></div>'}</section>
    <section class="grid">
      <div class="panel table-panel">
        <h2>分拣结果</h2>
        <div class="table-wrap">
          <table class="data-table incoming-table">
            <thead><tr><th>文件</th><th>匹配文献</th><th>阅读状态</th><th>项目缺口</th><th>证据价值</th><th>建议动作</th></tr></thead>
            <tbody>{table_rows or '<tr><td colspan="6">暂无 incoming 文件。</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    </section>
"""
    html_text = render_shell(
        title="PDF 分拣",
        subtitle="扫描 incoming 文件夹，判断匹配文献、项目缺口、证据价值和下一步动作。",
        current="PDF分拣",
        body=body,
        output=path,
        module="阅读",
        meta=f"{html.escape(project)} · 生成时间 {html.escape(dt.datetime.now().isoformat(timespec='seconds'))}",
        footer="由 scripts/scan_incoming_pdfs.py 自动生成。",
    )
    write_text_preserving_generated_at(path, html_text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan project incoming full-text files and recommend safe next actions.")
    parser.add_argument("--project", default=active_project_slug())
    parser.add_argument("--incoming-dir", type=Path)
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    out_dir = project / "literature"
    csv_path = out_dir / "incoming_pdf_triage.csv"
    json_path = out_dir / "incoming_pdf_triage.json"
    md_path = out_dir / "incoming_pdf_triage.md"
    html_path = out_dir / "incoming_pdf_triage.html"

    rows = build_rows(args.project, args.incoming_dir)
    write_csv(csv_path, rows)
    write_json(json_path, rows)
    write_md(md_path, args.project, rows, csv_path, html_path)
    write_html(html_path, args.project, rows, csv_path, json_path, md_path)
    print(f"Wrote incoming triage CSV: {csv_path}")
    print(f"Wrote incoming triage JSON: {json_path}")
    print(f"Wrote incoming triage markdown: {md_path}")
    print(f"Wrote incoming triage HTML: {html_path}")
    print(f"Items: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
