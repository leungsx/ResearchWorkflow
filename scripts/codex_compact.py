#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / "codex"
STATE_DIR = CODEX / "state"
VAULT = ROOT / "vault"
DAILY_DIR = VAULT / "07_Codex_Logs" / "daily"
COMPACT_DIR = VAULT / "07_Codex_Logs" / "compact_daily"
WEEKLY_DIR = VAULT / "08_Weekly_Reviews"
PACK_DIR = VAULT / "09_Context_Packs"

SECTION_ORDER = [
    "User Goals",
    "Discussion Summary",
    "Decisions",
    "Files Created or Modified",
    "Literature / Sources",
    "Experiments / Commands",
    "Open Questions",
    "Next Actions",
    "User Model Signals",
]

HOT_STATE_FILES = [
    STATE_DIR / "current_context.md",
    STATE_DIR / "open_loops.md",
    STATE_DIR / "user_model.md",
    STATE_DIR / "context_index.md",
]


def parse_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return dt.date.today()


def daily_path(day: dt.date) -> Path:
    return DAILY_DIR / f"{day.isoformat()}.md"


def compact_path(day: dt.date) -> Path:
    return COMPACT_DIR / f"{day.isoformat()}-summary.md"


def word_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").split())


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return sections


def meaningful_lines(lines: list[str], max_items: int) -> list[str]:
    kept: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("|") and "---" in line:
            continue
        if len(line) > 260:
            line = line[:257].rstrip() + "..."
        if not line.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
            line = f"- {line}"
        kept.append(line)
        if len(kept) >= max_items:
            break
    return kept


def recent_entry_lines(sections: dict[str, list[str]], max_items: int) -> list[str]:
    entries = [
        (name, lines)
        for name, lines in sections.items()
        if name.startswith("Entry -") or name.startswith("Fastlane Closeout -")
    ]
    kept: list[str] = []
    for name, lines in entries[-max_items:]:
        parts = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("- Kind:"):
                parts.append(line.replace("- Kind:", "kind:").strip())
            elif line.startswith("- Summary:"):
                summary = line.replace("- Summary:", "summary:").strip()
                if len(summary) > 220:
                    summary = summary[:217].rstrip() + "..."
                parts.append(summary)
            elif line.startswith("- Next actions:"):
                next_actions = line.replace("- Next actions:", "next:").strip()
                if len(next_actions) > 180:
                    next_actions = next_actions[:177].rstrip() + "..."
                parts.append(next_actions)
            elif line.startswith("- Mode:"):
                parts.append(line.replace("- Mode:", "mode:").strip())
        if parts:
            label = name.replace("Entry - ", "").replace("Fastlane Closeout - ", "")
            kept.append(f"- {label}: " + " | ".join(parts))
    return kept


def compact_daily(day: dt.date, max_items: int = 8) -> Path:
    source = daily_path(day)
    if not source.exists():
        raise FileNotFoundError(f"Daily log not found: {source}")

    text = source.read_text(encoding="utf-8", errors="ignore")
    sections = parse_sections(text)
    raw_words = len(text.split())

    output = [
        f"# Compact Daily Summary - {day.isoformat()}",
        "",
        "This is a lightweight routing summary. Keep the raw daily log as cold",
        "archive and read it only when a task needs exact chronology or details.",
        "",
        "## Source",
        "",
        f"- Raw log: `{source}`",
        f"- Raw word count: {raw_words}",
        f"- Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    for section in SECTION_ORDER:
        lines = meaningful_lines(sections.get(section, []), max_items=max_items)
        if not lines:
            continue
        output.append(f"## {section}")
        output.append("")
        output.extend(lines)
        output.append("")

    entries = recent_entry_lines(sections, max_items=max_items)
    if entries:
        output.append("## Recent Entries")
        output.append("")
        output.extend(entries)
        output.append("")

    output.extend(
        [
            "## Default Read Policy",
            "",
            "- Read this compact summary before the raw daily log.",
            "- Read the raw daily log only for exact command chronology, file-by-file audit, or disputed details.",
            "- Promote durable cross-day facts into `codex/state/current_context.md` instead of re-reading old logs.",
            "",
        ]
    )

    COMPACT_DIR.mkdir(parents=True, exist_ok=True)
    target = compact_path(day)
    target.write_text("\n".join(output), encoding="utf-8")
    return target


def daily_dates() -> list[dt.date]:
    dates: list[dt.date] = []
    for path in sorted(DAILY_DIR.glob("*.md")):
        try:
            dates.append(dt.date.fromisoformat(path.stem))
        except ValueError:
            continue
    return dates


def compact_all(before: str | None, max_items: int) -> list[Path]:
    before_day = dt.date.fromisoformat(before) if before else None
    written: list[Path] = []
    for day in daily_dates():
        if before_day and day >= before_day:
            continue
        written.append(compact_daily(day, max_items=max_items))
    return written


def write_index() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    COMPACT_DIR.mkdir(parents=True, exist_ok=True)
    target = STATE_DIR / "context_index.md"
    today = dt.date.today()

    compact_files = sorted(COMPACT_DIR.glob("*-summary.md"), reverse=True)
    daily_files = sorted(DAILY_DIR.glob("*.md"), reverse=True)
    weekly_files = sorted(WEEKLY_DIR.glob("20*-W*.md"), reverse=True)
    pack_files = sorted(PACK_DIR.glob("*-context-pack.md"), reverse=True)

    lines = [
        "# Context Index",
        "",
        f"Last updated: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Default Startup Read Order",
        "",
        "Read hot state first. Do not scan old raw logs unless the current task needs exact detail.",
        "",
    ]

    for path in HOT_STATE_FILES:
        status = "present" if path.exists() or path == target else "missing"
        lines.append(f"- {status}: `{path}`")

    lines.extend(
        [
            "",
            "## Today",
            "",
            f"- Daily log: `{daily_path(today)}`",
            f"- Compact summary: `{compact_path(today)}`" if compact_path(today).exists() else "- Compact summary: missing",
            "",
            "## Recent Compact Daily Summaries",
            "",
        ]
    )

    if compact_files:
        for path in compact_files[:14]:
            lines.append(f"- `{path.name}` ({word_count(path)} words)")
    else:
        lines.append("- None yet. Run `make codex-compact`.")

    lines.extend(["", "## Recent Context Packs", ""])
    for path in pack_files[:8]:
        lines.append(f"- `{path.name}` ({word_count(path)} words)")

    lines.extend(["", "## Recent Weekly Reviews", ""])
    for path in weekly_files[:8]:
        lines.append(f"- `{path.name}` ({word_count(path)} words)")

    lines.extend(
        [
            "",
            "## Cold Raw Daily Logs",
            "",
            "These are preserved for audit and exact reconstruction, but are not default startup context.",
            "",
        ]
    )
    for path in daily_files[:30]:
        compact = compact_path(dt.date.fromisoformat(path.stem))
        summary_status = "summary" if compact.exists() else "no-summary"
        lines.append(f"- `{path.name}` ({word_count(path)} words, {summary_status})")

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def audit() -> None:
    print("# Codex Context Audit\n")
    print("## Hot State")
    for path in HOT_STATE_FILES:
        if path.exists():
            print(f"- {path}: {word_count(path)} words")
        else:
            print(f"- {path}: missing")

    print("\n## Daily Logs")
    for day in daily_dates():
        raw = daily_path(day)
        compact = compact_path(day)
        status = "summary present" if compact.exists() else "summary missing"
        print(f"- {raw.name}: {word_count(raw)} words ({status})")

    print("\n## Recommendation")
    print("- Keep `current_context.md`, `open_loops.md`, `user_model.md`, and `context_index.md` as startup context.")
    print("- Compact daily logs after substantive turns or when raw logs exceed roughly 800 words.")
    print("- Move only durable cross-day facts into `current_context.md`; leave chronology in cold logs.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact Codex logs into lightweight startup context.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_compact = sub.add_parser("compact", help="Compact one daily log. Defaults to today.")
    p_compact.add_argument("--date", help="YYYY-MM-DD")
    p_compact.add_argument("--max-items", type=int, default=5)

    p_all = sub.add_parser("compact-all", help="Compact all daily logs, optionally before a date.")
    p_all.add_argument("--before", help="YYYY-MM-DD; compact logs strictly before this date")
    p_all.add_argument("--max-items", type=int, default=5)

    sub.add_parser("index", help="Write codex/state/context_index.md")
    sub.add_parser("audit", help="Print context word counts and compaction status")

    args = parser.parse_args()
    if args.command == "compact":
        target = compact_daily(parse_date(args.date), max_items=args.max_items)
        index = write_index()
        print(f"Wrote compact summary: {target}")
        print(f"Updated context index: {index}")
    elif args.command == "compact-all":
        targets = compact_all(args.before, max_items=args.max_items)
        index = write_index()
        print(f"Wrote {len(targets)} compact summaries.")
        for target in targets:
            print(f"- {target}")
        print(f"Updated context index: {index}")
    elif args.command == "index":
        print(f"Updated context index: {write_index()}")
    elif args.command == "audit":
        audit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
