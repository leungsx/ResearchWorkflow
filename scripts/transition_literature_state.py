#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
SCHEMA = ROOT / "schemas" / "literature_state.schema.yaml"
EVENT_LOG = ROOT / "vault" / "07_Codex_Logs" / "literature_events.jsonl"


def parse_state_schema(path: Path = SCHEMA) -> dict[str, Any]:
    states: list[str] = []
    transitions: dict[str, list[str]] = {}
    accepted: list[str] = []
    blocked: list[str] = []
    event_log = str(EVENT_LOG.relative_to(ROOT))
    section: str | None = None
    current_transition: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw_line.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            current_transition = None
            continue
        if not raw_line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            if key == "event_log":
                event_log = value.strip()
            continue
        if section in {"states", "accepted_for_manuscript_evidence", "blocked_for_manuscript_evidence"} and stripped.startswith("- "):
            target = states if section == "states" else accepted if section == "accepted_for_manuscript_evidence" else blocked
            target.append(stripped[2:].strip())
            continue
        if section == "allowed_transitions":
            if raw_line.startswith("  ") and not raw_line.startswith("    ") and stripped.endswith(":"):
                current_transition = stripped[:-1]
                transitions[current_transition] = []
            elif raw_line.startswith("    ") and stripped.startswith("- ") and current_transition:
                transitions[current_transition].append(stripped[2:].strip())
    return {
        "states": states,
        "allowed_transitions": transitions,
        "accepted_for_manuscript_evidence": accepted,
        "blocked_for_manuscript_evidence": blocked,
        "event_log": event_log,
    }


def read_matrix(path: Path = MATRIX) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_matrix(fieldnames: list[str], rows: list[dict[str, str]], path: Path = MATRIX) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def transition_allowed(schema: dict[str, Any], current: str, target: str) -> bool:
    if current == target:
        return True
    transitions = schema.get("allowed_transitions", {})
    if not isinstance(transitions, dict):
        return False
    return target in transitions.get(current, [])


def append_event(event: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transition a literature_matrix read_status through the canonical state machine.")
    parser.add_argument("--citekey", required=True)
    parser.add_argument("--to", required=True, dest="target_status")
    parser.add_argument("--from-status", dest="expected_from")
    parser.add_argument("--reason", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    schema = parse_state_schema()
    states = set(schema["states"])
    if args.target_status not in states:
        raise SystemExit(f"Unknown target status: {args.target_status}")

    fieldnames, rows = read_matrix()
    if "read_status" not in fieldnames:
        raise SystemExit("literature_matrix.csv is missing read_status")

    matches = [row for row in rows if row.get("citekey") == args.citekey]
    if len(matches) != 1:
        raise SystemExit(f"Expected one matrix row for {args.citekey}, found {len(matches)}")
    row = matches[0]
    current = (row.get("read_status") or "metadata-only").strip()
    if current not in states:
        raise SystemExit(f"Current status is not in state schema: {current}")
    if args.expected_from and current != args.expected_from:
        raise SystemExit(f"Current status mismatch for {args.citekey}: expected {args.expected_from}, actual {current}")
    if not transition_allowed(schema, current, args.target_status):
        raise SystemExit(f"Illegal transition for {args.citekey}: {current} -> {args.target_status}")

    event = {
        "schema_version": "ResearchWorkflow.LiteratureStateEvent.v1",
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "citekey": args.citekey,
        "project": args.project,
        "from_status": current,
        "to_status": args.target_status,
        "reason": args.reason,
        "evidence": args.evidence,
        "matrix_path": str(MATRIX.relative_to(ROOT)),
        "git_commit": git_commit(),
        "dry_run": args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(event, ensure_ascii=False, indent=2))
        return 0

    row["read_status"] = args.target_status
    write_matrix(fieldnames, rows)
    event_log = ROOT / str(schema.get("event_log") or EVENT_LOG.relative_to(ROOT))
    append_event(event, event_log)
    print(f"Transitioned {args.citekey}: {current} -> {args.target_status}")
    print(f"Appended event: {event_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
