#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"
RUNTIME_DIR = ROOT / "codex" / "runtime"
LEDGER = RUNTIME_DIR / "quick_events.jsonl"
DAILY_DIR = ROOT / "vault" / "07_Codex_Logs" / "daily"
COMPACT_DIR = ROOT / "vault" / "07_Codex_Logs" / "compact_daily"
SWEEP_DIR = ROOT / "vault" / "07_Codex_Logs" / "file_sweeps"
RECOMMEND_DIR = ROOT / "vault" / "15_CNKI_Frontier" / "daily_recommendations"


def today_iso(value: str | None = None) -> str:
    return value or dt.date.today().isoformat()


def rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_int(value: Any) -> int:
    text = clean(value).replace(",", "")
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else 0


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_matrix(project: str) -> list[dict[str, str]]:
    if not MATRIX.exists():
        return []
    with MATRIX.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        row
        for row in rows
        if row.get("source_database", "").upper() == "CNKI"
        and project in row.get("project_tags", "")
    ]


def latest_daily_state(project: str) -> dict[str, Any]:
    state = read_json(PROJECTS / project / "literature" / "daily_learning_state.json", {"history": []})
    history = sorted(state.get("history", []), key=lambda item: item.get("date", ""))
    return history[-1] if history else {}


def latest_recommendation_file(project: str, day: str) -> Path | None:
    candidates = sorted(
        RECOMMEND_DIR.glob(f"{day}-{project}*.md"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        candidates = sorted(
            RECOMMEND_DIR.glob(f"*-{project}*.md"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
    return candidates[0] if candidates else None


def extract_evidence_summary(project: str) -> dict[str, str]:
    path = PROJECTS / project / "manuscript" / "evidence_gate_report.md"
    if not path.exists():
        return {"path": rel(path), "status": "missing", "error": "", "warn": ""}
    text = path.read_text(encoding="utf-8", errors="ignore")

    def metric(name: str) -> str:
        match = re.search(rf"\|\s*{re.escape(name)}\s*\|\s*([^|]+?)\s*\|", text)
        return clean(match.group(1)) if match else ""

    return {
        "path": rel(path),
        "status": metric("Status") or "unknown",
        "error": metric("ERROR issues"),
        "warn": metric("WARN issues"),
    }


def count_existing(paths: list[str]) -> int:
    count = 0
    for value in paths:
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            count += 1
    return count


def next_candidate(project: str, topic: str, day: str) -> dict[str, Any] | None:
    import sys

    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        import cnki_daily_recommend as cdr
    except Exception:
        return None

    rows = cdr.load_matrix(MATRIX, project)
    metadata, _ = cdr.load_export_metadata(project)
    profile, _, _ = cdr.ensure_profile(project, topic, None)
    if topic and not profile.get("topic"):
        profile["topic"] = topic
    state, _ = cdr.load_state(project)
    stage = cdr.auto_stage(profile, state, day)
    ranked = cdr.rank_candidates(rows, metadata, profile, project, stage, day, state)
    if not ranked:
        return None
    item = ranked[0]
    return {
        "stage": stage,
        "citekey": item.citekey,
        "title": item.title,
        "year": item.row.get("year", ""),
        "source": item.row.get("source", ""),
        "score": f"{item.score:.1f}",
        "status": item.row.get("read_status", ""),
        "reader": rel(item.reader_path) if item.reader_path else "",
        "pdf": rel(item.pdf_path) if item.pdf_path else "",
        "reasons": item.reasons[:4],
    }


def render_snapshot(project: str, topic: str, day: str) -> str:
    rows = read_matrix(project)
    statuses = Counter(clean(row.get("read_status")) or "blank" for row in rows)
    readers = list((PROJECTS / project / "literature" / "readers").glob("*/paper.md"))
    context_packs = list((PROJECTS / project / "literature" / "context_packs").glob("*.md"))
    pdfs = count_existing([row.get("pdf_path", "") for row in rows])
    latest_state = latest_daily_state(project)
    latest_report = latest_recommendation_file(project, day)
    evidence = extract_evidence_summary(project)
    nxt = next_candidate(project, topic, day)

    lines = [
        f"# Fast Runtime Snapshot - {project}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Date: {day}",
        "",
        "This is the lightweight entry point for quick Codex turns. It is generated",
        "from canonical files and replaces repeated manual dashboard edits during micro-tasks.",
        "",
        "## Project Pulse",
        "",
        f"- CNKI matrix rows: {len(rows)}",
        f"- Local full texts recorded: {pdfs}",
        f"- Reader packages: {len(readers)}",
        f"- Token-light context packs: {len(context_packs)}",
        f"- Read statuses: "
        + ", ".join(f"`{key}`={value}" for key, value in sorted(statuses.items())),
        "",
        "## Latest Recommendation State",
        "",
    ]
    if latest_state:
        companions = latest_state.get("companions") or []
        lines.extend(
            [
                f"- Date: {latest_state.get('date', '')}",
                f"- Stage: `{latest_state.get('stage', '')}`",
                f"- Primary: `{latest_state.get('primary', '')}`",
                f"- Companions: {', '.join(f'`{item}`' for item in companions) if companions else 'none'}",
                f"- Report: `{latest_state.get('output', '')}`",
            ]
        )
    else:
        lines.append("- No daily recommendation state yet.")
    if latest_report:
        lines.append(f"- Latest report file: `{rel(latest_report)}`")

    lines.extend(["", "## Next Unread Candidate", ""])
    if nxt:
        lines.extend(
            [
                f"- Stage: `{nxt['stage']}`",
                f"- Citekey: `{nxt['citekey']}`",
                f"- Title: {nxt['title']}",
                f"- Year/source: {nxt['year']} / {nxt['source']}",
                f"- Score/read status: {nxt['score']} / `{nxt['status'] or 'blank'}`",
                f"- Reader: `{nxt['reader']}`" if nxt["reader"] else "- Reader: not generated",
                f"- PDF: `{nxt['pdf']}`" if nxt["pdf"] else "- PDF: not recorded",
            ]
        )
        if nxt["reasons"]:
            lines.append("- Reasons: " + "；".join(nxt["reasons"]))
    else:
        lines.append("- No ranked unread candidate found.")

    lines.extend(
        [
            "",
            "## Evidence Gate Cache",
            "",
            f"- Status: `{evidence['status']}`",
            f"- ERROR/WARN: {evidence.get('error') or '?'} / {evidence.get('warn') or '?'}",
            f"- Report: `{evidence['path']}`",
            "",
            "## Fast-Lane Rule",
            "",
            "- Recommendation-only or status-only tasks should update this snapshot and the quick ledger only.",
            "- Full dashboard, evidence gate, sweep, compact, and context-pack updates are reserved for evidence-changing or stage-closing tasks.",
            "",
        ]
    )
    return "\n".join(lines)


def command_snapshot(args: argparse.Namespace) -> int:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    day = today_iso(args.date)
    text = render_snapshot(args.project, args.topic or "", day)
    output = args.output or (RUNTIME_DIR / f"{args.project}_fast_snapshot.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote fast runtime snapshot: {output}")
    if args.print_snapshot:
        print()
        print(text)
    return 0


def append_event(args: argparse.Namespace) -> int:
    if not clean(args.summary):
        raise SystemExit("--summary is required")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "date": today_iso(args.date),
        "kind": args.kind,
        "project": args.project,
        "summary": clean(args.summary),
        "files": [item for item in args.file if clean(item)],
        "decisions": [clean(item) for item in args.decision if clean(item)],
        "open_loops": [clean(item) for item in args.open_loop if clean(item)],
        "next_actions": [clean(item) for item in args.next_action if clean(item)],
    }
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"Recorded quick event: {LEDGER}")
    return 0


def load_events(day: str, project: str | None = None) -> list[dict[str, Any]]:
    if not LEDGER.exists():
        return []
    events: list[dict[str, Any]] = []
    with LEDGER.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("date") != day:
                continue
            if project and item.get("project") not in {"", project}:
                continue
            events.append(item)
    return events


def ensure_daily(day: str) -> Path:
    path = DAILY_DIR / f"{day}.md"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Daily Codex Log - {day}\n\n"
            "## Session Index\n\n"
            "## User Goals\n\n"
            "## Discussion Summary\n\n"
            "## Decisions\n\n"
            "## Files Created or Modified\n\n"
            "## Literature / Sources\n\n"
            "## Experiments / Commands\n\n"
            "## Open Questions\n\n"
            "## Next Actions\n\n"
            "## User Model Signals\n",
            encoding="utf-8",
        )
    return path


def append_daily_entry(day: str, args: argparse.Namespace, events: list[dict[str, Any]]) -> Path:
    path = ensure_daily(day)
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    files: list[str] = []
    decisions: list[str] = []
    open_loops: list[str] = []
    next_actions: list[str] = []
    summaries: list[str] = []
    for event in events:
        summaries.append(event.get("summary", ""))
        files.extend(event.get("files", []) or [])
        decisions.extend(event.get("decisions", []) or [])
        open_loops.extend(event.get("open_loops", []) or [])
        next_actions.extend(event.get("next_actions", []) or [])
    if args.file:
        files.extend(args.file)
    if args.decision:
        decisions.extend(args.decision)
    if args.open_loop:
        open_loops.extend(args.open_loop)
    if args.next_action:
        next_actions.extend(args.next_action)

    def unique(items: list[str]) -> list[str]:
        seen: set[str] = set()
        kept: list[str] = []
        for item in items:
            item = clean(item)
            if item and item not in seen:
                seen.add(item)
                kept.append(item)
        return kept

    lines = [
        "",
        f"## Fastlane Closeout - {stamp}",
        "",
        f"- Mode: {args.mode}",
        f"- Project: {args.project or 'general'}",
        f"- Summary: {clean(args.summary)}",
    ]
    if summaries:
        lines.append("- Quick events:")
        for summary in summaries[-12:]:
            lines.append(f"  - {summary}")
    if unique(files):
        lines.append("- Files:")
        for item in unique(files)[:20]:
            lines.append(f"  - `{item}`")
    if unique(decisions):
        lines.append("- Decisions:")
        for item in unique(decisions)[:12]:
            lines.append(f"  - {item}")
    if unique(open_loops):
        lines.append("- Open loops:")
        for item in unique(open_loops)[:12]:
            lines.append(f"  - {item}")
    if unique(next_actions):
        lines.append("- Next actions:")
        for item in unique(next_actions)[:12]:
            lines.append(f"  - {item}")
    lines.append("")

    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path


def run_make(target: str) -> None:
    subprocess.run(["make", target], cwd=ROOT, check=False)


def command_close(args: argparse.Namespace) -> int:
    day = today_iso(args.date)
    events = load_events(day, args.project)
    daily = append_daily_entry(day, args, events)
    print(f"Appended fastlane closeout: {daily}")

    if args.snapshot and args.project:
        command_snapshot(
            argparse.Namespace(
                project=args.project,
                topic=args.topic or "",
                date=day,
                output=None,
                print_snapshot=False,
            )
        )

    sweep = args.sweep
    if sweep == "auto":
        sweep = "always" if args.mode in {"standard", "deep"} else "never"
    compact = args.compact
    if compact == "auto":
        compact = "always" if args.mode == "deep" else "never"

    if sweep == "always":
        run_make("codex-sweep")
    if compact == "always":
        run_make("codex-compact")
    return 0


def command_policy(_: argparse.Namespace) -> int:
    print(
        """# ResearchWorkflow Fastlane Policy

micro:
  examples: next paper recommendation, status check, path lookup, quick recap
  writes: codex/runtime snapshot + quick ledger
  avoids: sweep, compact, evidence gate, dashboard rewrites

standard:
  examples: paper read completed, PDF validated, matrix/read_status changed
  writes: canonical artifact + daily log closeout + visible board if user-facing
  runs: evidence gate when manuscript evidence may change; sweep at closeout

deep:
  examples: project milestone, weekly review, manuscript claims, submission package
  writes: hot context, open loops, context pack, compact summary, sweep
  runs: evidence gate, citation audit, passport when relevant
"""
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast-lane controls for lightweight research workflow tasks.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_snapshot = sub.add_parser("snapshot", help="Write a token-light runtime snapshot for one project.")
    p_snapshot.add_argument("--project", required=True)
    p_snapshot.add_argument("--topic", default="")
    p_snapshot.add_argument("--date")
    p_snapshot.add_argument("--output", type=Path)
    p_snapshot.add_argument("--print", dest="print_snapshot", action="store_true")
    p_snapshot.set_defaults(func=command_snapshot)

    p_event = sub.add_parser("event", help="Record a lightweight event without full archival overhead.")
    p_event.add_argument("--date")
    p_event.add_argument("--kind", default="micro")
    p_event.add_argument("--project", default="")
    p_event.add_argument("--summary", default="")
    p_event.add_argument("--file", action="append", default=[])
    p_event.add_argument("--decision", action="append", default=[])
    p_event.add_argument("--open-loop", action="append", default=[])
    p_event.add_argument("--next-action", action="append", default=[])
    p_event.set_defaults(func=append_event)

    p_close = sub.add_parser("close", help="Batch quick events into one daily-log closeout.")
    p_close.add_argument("--date")
    p_close.add_argument("--mode", choices=["fast", "standard", "deep"], default="fast")
    p_close.add_argument("--project", default="")
    p_close.add_argument("--topic", default="")
    p_close.add_argument("--summary", required=True)
    p_close.add_argument("--file", action="append", default=[])
    p_close.add_argument("--decision", action="append", default=[])
    p_close.add_argument("--open-loop", action="append", default=[])
    p_close.add_argument("--next-action", action="append", default=[])
    p_close.add_argument("--snapshot", action="store_true")
    p_close.add_argument("--sweep", choices=["auto", "never", "always"], default="auto")
    p_close.add_argument("--compact", choices=["auto", "never", "always"], default="auto")
    p_close.set_defaults(func=command_close)

    p_policy = sub.add_parser("policy", help="Print the workflow routing policy.")
    p_policy.set_defaults(func=command_policy)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
