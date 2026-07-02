from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rendering.paths import (
    ACTION_QUEUE_JSON,
    ARCHIVE_POLICY_JSON,
    ARTIFACT_MANIFEST,
    COLLABORATION_JSON,
    PROJECTS,
    REVIEW_STATE,
    ROOT,
    SEARCH_INDEX_JSON,
    WORKFLOW_AUDIT_JSON,
    WORKFLOW_STATE_JSON,
)


LITERATURE_MATRIX = ROOT / "library" / "literature_matrix.csv"
LITERATURE_MATRIX_SCHEMA = ROOT / "schemas" / "literature_matrix.schema.yaml"
CLAIM_EVIDENCE_LINKS_SCHEMA = ROOT / "schemas" / "claim_evidence_links.schema.yaml"


@dataclass
class SchemaIssue:
    path: str
    status: str
    message: str


@dataclass
class SchemaReport:
    checked_files: list[str]
    issues: list[SchemaIssue]


def rel(path: Path | str) -> str:
    item = Path(path)
    try:
        return str(item.relative_to(ROOT))
    except ValueError:
        return str(item)


def load_json(path: Path, issues: list[SchemaIssue], checked: list[str]) -> Any | None:
    checked.append(rel(path))
    if not path.exists():
        issues.append(SchemaIssue(rel(path), "FAIL", "文件不存在"))
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(SchemaIssue(rel(path), "FAIL", f"JSON 无效：{exc}"))
        return None


def add(issues: list[SchemaIssue], path: Path, status: str, message: str) -> None:
    issues.append(SchemaIssue(rel(path), status, message))


def require_keys(payload: dict[str, Any], path: Path, location: str, keys: list[str], issues: list[SchemaIssue]) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        add(issues, path, "FAIL", f"{location} 缺少字段：{', '.join(missing)}")


def require_type(payload: dict[str, Any], path: Path, key: str, expected: type | tuple[type, ...], issues: list[SchemaIssue], location: str = "") -> None:
    if key in payload and not isinstance(payload[key], expected):
        label = f"{location}.{key}" if location else key
        if isinstance(expected, tuple):
            names = " / ".join(item.__name__ for item in expected)
        else:
            names = expected.__name__
        add(issues, path, "FAIL", f"{label} 类型应为 {names}")


def require_existing_html(value: Any, path: Path, location: str, issues: list[SchemaIssue]) -> None:
    text = str(value or "")
    if not text.endswith(".html"):
        add(issues, path, "FAIL", f"{location} 必须指向 HTML：{text}")
        return
    if not (ROOT / text).exists():
        add(issues, path, "FAIL", f"{location} 指向不存在的 HTML：{text}")


def require_existing_path(value: Any, path: Path, location: str, issues: list[SchemaIssue]) -> None:
    text = str(value or "")
    if not text:
        add(issues, path, "FAIL", f"{location} 不能为空")
        return
    if not (ROOT / text).exists():
        add(issues, path, "FAIL", f"{location} 指向不存在的文件：{text}")


def schema_list(path: Path, key: str) -> list[str]:
    values: list[str] = []
    current: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if not raw_line.startswith(" ") and ":" in stripped:
            name, value = stripped.split(":", 1)
            current = name.strip() if not value.strip() else None
            continue
        if current == key and stripped.startswith("- "):
            values.append(stripped[2:].strip().strip("\"'"))
    return values


def validate_literature_matrix(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    checked.append(rel(path))
    if not path.exists():
        add(issues, path, "FAIL", "literature matrix 缺失")
        return
    expected = schema_list(LITERATURE_MATRIX_SCHEMA, "field_order")
    required = set(schema_list(LITERATURE_MATRIX_SCHEMA, "required_fields"))
    statuses = set(schema_list(LITERATURE_MATRIX_SCHEMA, "read_status_values"))
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if fields != expected:
            add(issues, path, "FAIL", "CSV 字段顺序或字段集合与 literature_matrix schema 不一致")
        seen: set[str] = set()
        rows = list(reader)
    for index, row in enumerate(rows, start=2):
        citekey = str(row.get("citekey", "")).strip()
        if citekey in seen:
            add(issues, path, "FAIL", f"第 {index} 行 citekey 重复：{citekey}")
        elif citekey:
            seen.add(citekey)
        for field in required:
            if not str(row.get(field, "")).strip():
                add(issues, path, "FAIL", f"第 {index} 行必填字段为空：{field}")
        status = str(row.get("read_status", "")).strip()
        if status and status not in statuses:
            add(issues, path, "FAIL", f"第 {index} 行 read_status 非法：{status}")


def validate_claim_evidence_links(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    checked.append(rel(path))
    expected = schema_list(CLAIM_EVIDENCE_LINKS_SCHEMA, "field_order")
    required = set(schema_list(CLAIM_EVIDENCE_LINKS_SCHEMA, "required_fields"))
    usage_values = set(schema_list(CLAIM_EVIDENCE_LINKS_SCHEMA, "evidence_usage_status_values"))
    if not path.exists():
        add(issues, path, "FAIL", "claim_evidence_links.csv 缺失")
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if fields != expected:
            add(issues, path, "FAIL", "CSV 字段顺序或字段集合与 claim_evidence_links schema 不一致")
        rows = list(reader)
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows, start=2):
        for field in required:
            if not str(row.get(field, "")).strip():
                add(issues, path, "FAIL", f"第 {index} 行必填字段为空：{field}")
        key = (row.get("claim_id", ""), row.get("citekey", ""), row.get("source_block_id", ""))
        if key in seen:
            add(issues, path, "FAIL", f"第 {index} 行重复 claim/citekey/source_block_id：{key}")
        seen.add(key)
        if str(row.get("used_in_manuscript", "")).strip().lower() not in {"true", "false"}:
            add(issues, path, "FAIL", f"第 {index} 行 used_in_manuscript 必须是 true/false")
        usage = str(row.get("evidence_usage_status", "")).strip()
        if usage_values and usage not in usage_values:
            add(issues, path, "FAIL", f"第 {index} 行 evidence_usage_status 非法：{usage}")


def validate_artifact_manifest(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    checked.append(rel(path))
    if not path.exists():
        add(issues, path, "FAIL", "artifact manifest 缺失")
        return
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = set(rows[0].keys()) if rows else set()
    required = {"source_path", "source_type", "display_path", "display_type", "title", "layer", "generated_by"}
    missing = sorted(required - fields)
    if missing:
        add(issues, path, "FAIL", "CSV 缺少字段：" + ", ".join(missing))
    if not rows:
        add(issues, path, "FAIL", "CSV 没有数据行")
        return
    for index, row in enumerate(rows, start=2):
        display = row.get("display_path", "")
        if not display.endswith(".html"):
            add(issues, path, "FAIL", f"第 {index} 行 display_path 不是 HTML：{display}")
        elif not (ROOT / display).exists():
            add(issues, path, "FAIL", f"第 {index} 行 display_path 不存在：{display}")


def validate_search_index(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "entry_count", "entries"], issues)
    require_type(payload, path, "entry_count", int, issues)
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        add(issues, path, "FAIL", "entries 必须是数组")
        return
    if payload.get("entry_count") != len(entries):
        add(issues, path, "FAIL", f"entry_count 与 entries 长度不一致：{payload.get('entry_count')} / {len(entries)}")
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            add(issues, path, "FAIL", f"entries[{index}] 必须是对象")
            continue
        require_keys(
            entry,
            path,
            f"entries[{index}]",
            ["id", "title", "layer", "display_type", "source_path", "display_path", "summary", "snippet_text", "keywords", "weight", "search_text"],
            issues,
        )
        require_type(entry, path, "keywords", list, issues, f"entries[{index}]")
        require_type(entry, path, "weight", int, issues, f"entries[{index}]")
        require_existing_html(entry.get("display_path"), path, f"entries[{index}].display_path", issues)


def validate_review_state(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "today", "queue_path", "summary", "focus_items", "due_items", "learned_items", "all_items"], issues)
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        add(issues, path, "FAIL", "summary 必须是对象")
        return
    for key in ["total_items", "due_count", "overdue_count", "upcoming_7_count", "future_count", "unscheduled_count", "learned_today_count"]:
        require_type(summary, path, key, int, issues, "summary")
    all_items = payload.get("all_items", [])
    due_items = payload.get("due_items", [])
    focus_items = payload.get("focus_items", [])
    if isinstance(all_items, list) and summary.get("total_items") != len(all_items):
        add(issues, path, "FAIL", f"summary.total_items 与 all_items 长度不一致：{summary.get('total_items')} / {len(all_items)}")
    if isinstance(due_items, list) and summary.get("due_count") != len(due_items):
        add(issues, path, "FAIL", f"summary.due_count 与 due_items 长度不一致：{summary.get('due_count')} / {len(due_items)}")
    learned_items = payload.get("learned_items", [])
    if isinstance(learned_items, list) and summary.get("learned_today_count") != len(learned_items):
        add(issues, path, "FAIL", f"summary.learned_today_count 与 learned_items 长度不一致：{summary.get('learned_today_count')} / {len(learned_items)}")
    for label, items in [("focus_items", focus_items), ("due_items", due_items), ("learned_items", learned_items), ("all_items", all_items)]:
        if not isinstance(items, list):
            add(issues, path, "FAIL", f"{label} 必须是数组")
            continue
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                add(issues, path, "FAIL", f"{label}[{index}] 必须是对象")
                continue
            require_keys(item, path, f"{label}[{index}]", ["id", "title", "type", "stage", "next_review", "status", "prompt", "display_path"], issues)
            require_existing_html(item.get("display_path"), path, f"{label}[{index}].display_path", issues)


def validate_project_state(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "project", "entrypoints", "literature", "review", "artifacts", "next_actions"], issues)
    project = payload.get("project", {})
    entrypoints = payload.get("entrypoints", {})
    literature = payload.get("literature", {})
    review = payload.get("review", {})
    artifacts = payload.get("artifacts", {})
    if isinstance(project, dict):
        require_keys(project, path, "project", ["slug", "title", "path", "dashboard"], issues)
        require_existing_path(project.get("dashboard"), path, "project.dashboard", issues)
    else:
        add(issues, path, "FAIL", "project 必须是对象")
    if isinstance(entrypoints, dict):
        for key in ["study_dashboard", "today", "project_dashboard", "review_today", "search", "project_collaboration", "archive_policy"]:
            require_existing_html(entrypoints.get(key), path, f"entrypoints.{key}", issues)
    else:
        add(issues, path, "FAIL", "entrypoints 必须是对象")
    if isinstance(literature, dict):
        for key in ["matrix_rows", "recorded_full_texts", "reader_packages", "context_packs"]:
            require_type(literature, path, key, int, issues, "literature")
    else:
        add(issues, path, "FAIL", "literature 必须是对象")
    if isinstance(review, dict):
        for key in ["due_count", "overdue_count", "upcoming_7_count"]:
            require_type(review, path, key, int, issues, "review")
        require_existing_html(review.get("review_today"), path, "review.review_today", issues)
    else:
        add(issues, path, "FAIL", "review 必须是对象")
    if isinstance(artifacts, dict):
        for key in ["artifact_manifest", "search_index"]:
            require_existing_path(artifacts.get(key), path, f"artifacts.{key}", issues)
    else:
        add(issues, path, "FAIL", "artifacts 必须是对象")


def validate_writing_traceability(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(
        payload,
        path,
        "root",
        ["schema_version", "generated_at", "project", "summary", "verification_queue_summary", "top_verification_tasks", "research_question_traces", "variable_traces", "paragraph_traces"],
        issues,
    )
    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        for key in ["claim_link_rows", "unique_claims", "page_located_rows", "page_pending_rows", "human_ready_rows"]:
            require_type(summary, path, key, int, issues, "summary")
    else:
        add(issues, path, "FAIL", "summary 必须是对象")
    queue_summary = payload.get("verification_queue_summary", {})
    if isinstance(queue_summary, dict):
        for key in ["total_items", "needs_page_locator", "needs_page_check", "needs_human_read", "ready_for_manuscript_review"]:
            require_type(queue_summary, path, key, int, issues, "verification_queue_summary")
    else:
        add(issues, path, "FAIL", "verification_queue_summary 必须是对象")
    top_tasks = payload.get("top_verification_tasks", [])
    if not isinstance(top_tasks, list) or not top_tasks:
        add(issues, path, "FAIL", "top_verification_tasks 必须是非空数组")
    else:
        for index, item in enumerate(top_tasks, start=1):
            if not isinstance(item, dict):
                add(issues, path, "FAIL", f"top_verification_tasks[{index}] 必须是对象")
                continue
            require_keys(item, path, f"top_verification_tasks[{index}]", ["task_id", "priority", "verification_status", "claim_id", "citekey", "source_block_id", "page", "read_status", "evidence_usage_status", "next_action"], issues)
    for list_key, required in [
        ("research_question_traces", ["slot", "question", "linked_claims", "source_trace", "readiness"]),
        ("variable_traces", ["layer", "candidate_indicators", "linked_claims", "source_trace", "boundary"]),
        ("paragraph_traces", ["slot", "purpose", "linked_claims", "source_trace", "readiness", "next_action"]),
    ]:
        items = payload.get(list_key, [])
        if not isinstance(items, list) or not items:
            add(issues, path, "FAIL", f"{list_key} 必须是非空数组")
            continue
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                add(issues, path, "FAIL", f"{list_key}[{index}] 必须是对象")
                continue
            require_keys(item, path, f"{list_key}[{index}]", required, issues)


def validate_page_verification_queue(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "project", "summary", "items"], issues)
    summary = payload.get("summary", {})
    items = payload.get("items", [])
    if isinstance(summary, dict):
        for key in ["total_items", "needs_page_locator", "needs_page_check", "needs_human_read", "ready_for_manuscript_review"]:
            require_type(summary, path, key, int, issues, "summary")
    else:
        add(issues, path, "FAIL", "summary 必须是对象")
    if not isinstance(items, list) or not items:
        add(issues, path, "FAIL", "items 必须是非空数组")
        return
    if isinstance(summary, dict) and summary.get("total_items") != len(items):
        add(issues, path, "FAIL", f"summary.total_items 与 items 长度不一致：{summary.get('total_items')} / {len(items)}")
    allowed_statuses = {"needs_page_locator", "needs_page_check", "needs_human_read", "ready_for_manuscript_review"}
    usage_values = set(schema_list(CLAIM_EVIDENCE_LINKS_SCHEMA, "evidence_usage_status_values"))
    required = [
        "task_id",
        "priority",
        "verification_status",
        "claim_id",
        "claim_text",
        "citekey",
        "source_block_id",
        "page",
        "locator_status",
        "read_status",
        "evidence_usage_status",
        "used_in_manuscript",
        "risk",
        "source_path",
        "reader_display_path",
        "next_action",
    ]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            add(issues, path, "FAIL", f"items[{index}] 必须是对象")
            continue
        require_keys(item, path, f"items[{index}]", required, issues)
        if str(item.get("verification_status", "")) not in allowed_statuses:
            add(issues, path, "FAIL", f"items[{index}].verification_status 非法：{item.get('verification_status')}")
        if not str(item.get("priority", "")).isdigit():
            add(issues, path, "FAIL", f"items[{index}].priority 必须是数字字符串")
        if str(item.get("used_in_manuscript", "")).lower() not in {"true", "false"}:
            add(issues, path, "FAIL", f"items[{index}].used_in_manuscript 必须是 true/false")
        usage = str(item.get("evidence_usage_status", "")).strip()
        if usage_values and usage not in usage_values:
            add(issues, path, "FAIL", f"items[{index}].evidence_usage_status 非法：{usage}")
        display = str(item.get("reader_display_path", ""))
        if display:
            require_existing_html(display, path, f"items[{index}].reader_display_path", issues)
        source = str(item.get("source_path", ""))
        if source:
            require_existing_path(source, path, f"items[{index}].source_path", issues)


def validate_workflow_state(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "entrypoints", "counts", "audit", "review", "graph", "projects", "artifacts", "next_actions"], issues)
    entrypoints = payload.get("entrypoints", {})
    if isinstance(entrypoints, dict):
        for key in ["study_dashboard", "today", "review_today", "knowledge_graph", "search", "workflow_health", "workflow_state", "action_queue", "project_collaboration", "archive_policy"]:
            require_existing_html(entrypoints.get(key), path, f"entrypoints.{key}", issues)
    else:
        add(issues, path, "FAIL", "entrypoints 必须是对象")
    counts = payload.get("counts", {})
    if isinstance(counts, dict):
        for key in ["manifest_rows", "search_entries", "project_count", "git_dirty_paths"]:
            require_type(counts, path, key, int, issues, "counts")
    audit = payload.get("audit", {})
    if isinstance(audit, dict):
        require_keys(audit, path, "audit", ["counts", "checks", "health_html", "report_json"], issues)
        require_existing_html(audit.get("health_html"), path, "audit.health_html", issues)
        require_existing_path(audit.get("report_json"), path, "audit.report_json", issues)
    projects = payload.get("projects", [])
    if isinstance(projects, list):
        for index, project in enumerate(projects, start=1):
            if not isinstance(project, dict):
                add(issues, path, "FAIL", f"projects[{index}] 必须是对象")
                continue
            require_keys(project, path, f"projects[{index}]", ["slug", "title", "matrix_rows", "reader_packages", "state_path", "dashboard_html"], issues)
            require_existing_path(project.get("state_path"), path, f"projects[{index}].state_path", issues)
            require_existing_html(project.get("dashboard_html"), path, f"projects[{index}].dashboard_html", issues)
    else:
        add(issues, path, "FAIL", "projects 必须是数组")


def validate_action_queue(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "source_state", "entrypoint", "summary", "actions"], issues)
    require_existing_html(payload.get("entrypoint"), path, "entrypoint", issues)
    require_existing_path(payload.get("source_state"), path, "source_state", issues)
    actions = payload.get("actions", [])
    summary = payload.get("summary", {})
    if not isinstance(actions, list):
        add(issues, path, "FAIL", "actions 必须是数组")
        return
    if isinstance(summary, dict) and summary.get("total_open") != len(actions):
        add(issues, path, "FAIL", f"summary.total_open 与 actions 长度不一致：{summary.get('total_open')} / {len(actions)}")
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            add(issues, path, "FAIL", f"actions[{index}] 必须是对象")
            continue
        require_keys(action, path, f"actions[{index}]", ["id", "kind", "priority", "title", "reason", "entrypoint", "status", "rank"], issues)
        require_type(action, path, "priority", int, issues, f"actions[{index}]")
        require_type(action, path, "rank", int, issues, f"actions[{index}]")
        require_existing_html(action.get("entrypoint"), path, f"actions[{index}].entrypoint", issues)


def validate_audit_report(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "date", "summary", "reports", "checks"], issues)
    reports = payload.get("reports", {})
    if isinstance(reports, dict):
        require_existing_path(reports.get("markdown"), path, "reports.markdown", issues)
        require_existing_html(reports.get("html"), path, "reports.html", issues)
    else:
        add(issues, path, "FAIL", "reports 必须是对象")
    checks = payload.get("checks", [])
    summary = payload.get("summary", {})
    if not isinstance(checks, list):
        add(issues, path, "FAIL", "checks 必须是数组")
        return
    if isinstance(summary, dict):
        counts = summary.get("counts", {})
        if not isinstance(counts, dict):
            add(issues, path, "FAIL", "summary.counts 必须是对象")
        else:
            for status in ["PASS", "WARN", "FAIL"]:
                if counts.get(status) != sum(1 for check in checks if isinstance(check, dict) and check.get("status") == status):
                    add(issues, path, "FAIL", f"summary.counts.{status} 与 checks 不一致")
    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            add(issues, path, "FAIL", f"checks[{index}] 必须是对象")
            continue
        require_keys(check, path, f"checks[{index}]", ["area", "status", "title", "detail"], issues)
        if check.get("status") not in {"PASS", "WARN", "FAIL"}:
            add(issues, path, "FAIL", f"checks[{index}].status 非法：{check.get('status')}")


def validate_collaboration_state(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "entrypoint", "summary", "roles", "entrypoints", "projects"], issues)
    require_existing_html(payload.get("entrypoint"), path, "entrypoint", issues)
    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        for key in ["project_count", "user_waiting", "codex_ready", "open_actions"]:
            require_type(summary, path, key, int, issues, "summary")
    projects = payload.get("projects", [])
    if not isinstance(projects, list):
        add(issues, path, "FAIL", "projects 必须是数组")
        return
    if isinstance(summary, dict) and summary.get("project_count") != len(projects):
        add(issues, path, "FAIL", f"summary.project_count 与 projects 长度不一致：{summary.get('project_count')} / {len(projects)}")
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            add(issues, path, "FAIL", f"projects[{index}] 必须是对象")
            continue
        require_keys(project, path, f"projects[{index}]", ["slug", "title", "stage", "state_path", "entrypoints", "user_handoffs", "codex_handoffs"], issues)
        require_existing_path(project.get("state_path"), path, f"projects[{index}].state_path", issues)
        entrypoints = project.get("entrypoints", {})
        if isinstance(entrypoints, dict):
            for key, value in entrypoints.items():
                if value:
                    require_existing_html(value, path, f"projects[{index}].entrypoints.{key}", issues)


def validate_archive_policy(path: Path, issues: list[SchemaIssue], checked: list[str]) -> None:
    payload = load_json(path, issues, checked)
    if not isinstance(payload, dict):
        add(issues, path, "FAIL", "顶层结构必须是对象")
        return
    require_keys(payload, path, "root", ["schema_version", "generated_at", "entrypoint", "summary", "policy", "entrypoints", "backups", "logs", "generated", "caches", "actions"], issues)
    require_existing_html(payload.get("entrypoint"), path, "entrypoint", issues)
    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        for key in ["backup_count", "backup_prune_candidates", "daily_log_count", "compact_candidates", "cache_candidates", "generated_html_count"]:
            require_type(summary, path, key, int, issues, "summary")
    actions = payload.get("actions", [])
    if not isinstance(actions, list):
        add(issues, path, "FAIL", "actions 必须是数组")
        return
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            add(issues, path, "FAIL", f"actions[{index}] 必须是对象")
            continue
        require_keys(action, path, f"actions[{index}]", ["id", "title", "mode", "command", "reason", "candidate_count"], issues)
        require_type(action, path, "candidate_count", int, issues, f"actions[{index}]")


def validate_workflow_schemas(include_audit_report: bool = True) -> SchemaReport:
    checked: list[str] = []
    issues: list[SchemaIssue] = []
    validators = [
        (LITERATURE_MATRIX, validate_literature_matrix),
        (ARTIFACT_MANIFEST, validate_artifact_manifest),
        (SEARCH_INDEX_JSON, validate_search_index),
        (REVIEW_STATE, validate_review_state),
        (WORKFLOW_STATE_JSON, validate_workflow_state),
        (ACTION_QUEUE_JSON, validate_action_queue),
        (COLLABORATION_JSON, validate_collaboration_state),
        (ARCHIVE_POLICY_JSON, validate_archive_policy),
    ]
    if include_audit_report:
        validators.append((WORKFLOW_AUDIT_JSON, validate_audit_report))
    for path in sorted(PROJECTS.glob("*/project_state.json")):
        validators.append((path, validate_project_state))
    for path in sorted(PROJECTS.glob("*/evidence/claim_evidence_links.csv")):
        validators.append((path, validate_claim_evidence_links))
    for path in sorted(PROJECTS.glob("*/evidence/claim_evidence_candidates.csv")):
        validators.append((path, validate_claim_evidence_links))
    for path in sorted(PROJECTS.glob("*/evidence/page_verification_queue.json")):
        validators.append((path, validate_page_verification_queue))
    for path in sorted(PROJECTS.glob("*/manuscript/writing_traceability.json")):
        validators.append((path, validate_writing_traceability))
    for path, validator in validators:
        validator(path, issues, checked)
    return SchemaReport(checked_files=checked, issues=issues)


def status_counts(issues: list[SchemaIssue]) -> dict[str, int]:
    return {status: sum(1 for issue in issues if issue.status == status) for status in ["PASS", "WARN", "FAIL"]}
