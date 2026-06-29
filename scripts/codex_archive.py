#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / "codex"
VAULT = ROOT / "vault"
DAILY_DIR = VAULT / "07_Codex_Logs" / "daily"
WEEKLY_DIR = VAULT / "08_Weekly_Reviews"
PACK_DIR = VAULT / "09_Context_Packs"
USER_MODEL_DIR = VAULT / "10_User_Model"
STATE_DIR = CODEX / "state"
COMPACT_DIR = VAULT / "07_Codex_Logs" / "compact_daily"


def parse_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return dt.date.today()


def week_id(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def read_template(name: str) -> str:
    return (CODEX / "templates" / name).read_text(encoding="utf-8")


def ensure_file(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def daily_path(day: dt.date) -> Path:
    return DAILY_DIR / f"{day.isoformat()}.md"


def weekly_path(day: dt.date) -> Path:
    return WEEKLY_DIR / f"{week_id(day)}.md"


def context_pack_path(day: dt.date) -> Path:
    return PACK_DIR / f"{day.isoformat()}-context-pack.md"


def compact_daily_path(day: dt.date) -> Path:
    return COMPACT_DIR / f"{day.isoformat()}-summary.md"


def render_daily(day: dt.date) -> str:
    return read_template("Daily Codex Log.md").replace("{{DATE}}", day.isoformat())


def render_weekly(day: dt.date) -> str:
    return read_template("Weekly Codex Review.md").replace("{{WEEK}}", week_id(day))


def render_context(day: dt.date) -> str:
    return read_template("Context Pack.md").replace("{{DATE}}", day.isoformat())


def start(args: argparse.Namespace) -> int:
    day = parse_date(args.date)
    created = []
    if ensure_file(daily_path(day), render_daily(day)):
        created.append(daily_path(day))
    if ensure_file(weekly_path(day), render_weekly(day)):
        created.append(weekly_path(day))
    if ensure_file(context_pack_path(day), render_context(day)):
        created.append(context_pack_path(day))
    USER_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("# Codex Research Session Start")
    print(f"Date: {day.isoformat()}")
    print(f"Week: {week_id(day)}")
    print("\nDefault startup context (hot):")
    print(f"- {STATE_DIR / 'current_context.md'}")
    print(f"- {STATE_DIR / 'open_loops.md'}")
    print(f"- {STATE_DIR / 'user_model.md'}")
    context_index = STATE_DIR / "context_index.md"
    if context_index.exists():
        print(f"- {context_index}")

    print("\nRead for today's exact details only when needed:")
    if compact_daily_path(day).exists():
        print(f"- {compact_daily_path(day)}")
        print(f"- {daily_path(day)} (cold raw log)")
    else:
        print(f"- {daily_path(day)}")
    print(f"- {weekly_path(day)}")
    if created:
        print("\nCreated:")
        for path in created:
            print(f"- {path}")
    return 0


def append(args: argparse.Namespace) -> int:
    day = parse_date(args.date)
    path = daily_path(day)
    ensure_file(path, render_daily(day))
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    lines = [
        "",
        f"## Entry - {stamp}",
        "",
        f"- Kind: {args.kind}",
        f"- Summary: {args.summary}",
    ]
    if args.files:
        lines.append(f"- Files: {args.files}")
    if args.decisions:
        lines.append(f"- Decisions: {args.decisions}")
    if args.open_loops:
        lines.append(f"- Open loops: {args.open_loops}")
    if args.next_actions:
        lines.append(f"- Next actions: {args.next_actions}")
    lines.append("")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    print(f"Appended daily log entry: {path}")
    return 0


def weekly(args: argparse.Namespace) -> int:
    day = parse_date(args.date)
    path = weekly_path(day)
    ensure_file(path, render_weekly(day))
    year, week, _ = day.isocalendar()
    daily_logs = []
    for item in sorted(DAILY_DIR.glob("*.md")):
        try:
            item_day = dt.date.fromisoformat(item.stem)
        except ValueError:
            continue
        if item_day.isocalendar()[:2] == (year, week):
            daily_logs.append(item)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Daily Logs Included\n\n")
        for item in daily_logs:
            handle.write(f"- {item}\n")
    print(f"Updated weekly review scaffold: {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain Codex-first research logs and context packs.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Create and print today's research session context files.")
    p_start.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    p_start.set_defaults(func=start)

    p_append = sub.add_parser("append", help="Append a structured entry to today's daily log.")
    p_append.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    p_append.add_argument("--kind", default="session")
    p_append.add_argument("--summary", required=True)
    p_append.add_argument("--files", default="")
    p_append.add_argument("--decisions", default="")
    p_append.add_argument("--open-loops", default="")
    p_append.add_argument("--next-actions", default="")
    p_append.set_defaults(func=append)

    p_weekly = sub.add_parser("weekly", help="Create/update the current weekly review scaffold.")
    p_weekly.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    p_weekly.set_defaults(func=weekly)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
