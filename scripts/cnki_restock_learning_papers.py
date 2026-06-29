#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import cnki_daily_recommend as daily


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "library" / "cnki_exports"
FULLTEXT_SUFFIXES = {".pdf", ".caj", ".nh", ".kdh"}


def clean(value: str | None) -> str:
    return daily.clean(value)


def default_export_path(project: str, stem: str) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return EXPORT_DIR / project / f"{stem}_{timestamp}.json"


def local_fulltext_path(row: dict[str, str], target_dir: Path) -> Path | None:
    path = daily.resolve_path(row.get("pdf_path", ""))
    if path and path.exists() and path.suffix.lower() in FULLTEXT_SUFFIXES:
        return path

    citekey = clean(row.get("citekey"))
    if not citekey:
        return None

    candidates = [target_dir / f"{citekey}{suffix}" for suffix in sorted(FULLTEXT_SUFFIXES)]
    candidates.append(target_dir / "converted" / f"{citekey}.pdf")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def local_fulltext_count(rows: list[dict[str, str]], target_dir: Path) -> int:
    return sum(1 for row in rows if local_fulltext_path(row, target_dir))


def select_candidates(
    project: str,
    topic: str,
    stage: str,
    current_date: str,
    refill_count: int,
    target_dir: Path,
    profile_path: Path | None,
) -> tuple[list[daily.Candidate], dict, Path, list[dict[str, str]], dict[str, dict[str, str]]]:
    profile, resolved_profile_path, _ = daily.ensure_profile(project, topic, profile_path)
    state, _ = daily.load_state(project)
    stage_value = daily.auto_stage(profile, state, current_date) if stage == "auto" else stage
    rows = daily.load_matrix(daily.MATRIX, project)
    metadata, _ = daily.load_export_metadata(project)
    ranked = daily.rank_candidates(rows, metadata, profile, project, stage_value, current_date, state)

    chosen: list[daily.Candidate] = []
    for candidate in ranked:
        if local_fulltext_path(candidate.row, target_dir):
            continue
        if not clean(candidate.meta.get("detail_url")):
            continue
        chosen.append(candidate)
        if len(chosen) >= refill_count:
            break

    return chosen, profile, resolved_profile_path, rows, metadata


def build_selected_rows(candidates: list[daily.Candidate]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate in candidates:
        meta = candidate.meta
        row = candidate.row
        rows.append(
            {
                "title": row.get("title", ""),
                "year": row.get("year", "") or meta.get("year", ""),
                "detail_url": meta.get("detail_url", ""),
                "source": row.get("source", "") or meta.get("source", ""),
                "cited_count": meta.get("cited_count", ""),
                "download_count": meta.get("download_count", ""),
                "citekey": row.get("citekey", ""),
            }
        )
    return rows


def restock_command(
    selected_json: Path,
    project: str,
    current_count: int,
    attempt_count: int,
    target_dir: Path,
    args: argparse.Namespace,
) -> list[str]:
    cmd = [
        sys.executable,
        str(Path(__file__).with_name("cnki_batch_pdf_download.py")),
        "--metadata-json",
        str(selected_json),
        "--project",
        project,
        "--target-total",
        str(current_count + attempt_count),
        "--limit",
        str(attempt_count),
        "--target-dir",
        str(target_dir),
        "--update-matrix",
        "--delay-min",
        str(args.delay_min),
        "--delay-max",
        str(args.delay_max),
        "--timeout",
        str(args.timeout),
        "--nav-timeout",
        str(args.nav_timeout),
    ]
    if args.confirm_save_dialog:
        cmd.append("--confirm-save-dialog")
        cmd.extend(["--save-dialog-delay", str(args.save_dialog_delay)])
    if args.no_stop_on_barrier:
        cmd.append("--no-stop-on-barrier")
    if args.allow_non_pdf_fallback:
        cmd.append("--allow-non-pdf-fallback")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Maintain a CNKI learning-paper stock: when local full texts fall below a threshold, pick preferred candidates and trigger a refill download run."
    )
    parser.add_argument("--project", default="library_short_video")
    parser.add_argument("--topic", default="")
    parser.add_argument("--stage", choices=["auto", *daily.STAGE_ORDER], default="auto")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--min-stored", type=int, default=5, help="Only trigger a refill run when local full texts are below this threshold.")
    parser.add_argument("--refill-count", type=int, default=12, help="How many new papers to attempt when a refill is triggered. Keep this in the 10-15 range for the intended workflow.")
    parser.add_argument("--profile", type=Path, help="Optional recommendation profile JSON path.")
    parser.add_argument("--target-dir", type=Path, help="Directory for downloaded CNKI full texts. Defaults to library/pdfs/<project>.")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--nav-timeout", type=float, default=25.0)
    parser.add_argument("--delay-min", type=float, default=20.0)
    parser.add_argument("--delay-max", type=float, default=35.0)
    parser.add_argument("--confirm-save-dialog", action="store_true")
    parser.add_argument("--save-dialog-delay", type=float, default=1.2)
    parser.add_argument("--no-stop-on-barrier", action="store_true")
    parser.add_argument("--allow-non-pdf-fallback", action="store_true", help="Accept CAJ/NH/KDH as full-text stock when detail-page PDF is unavailable.")
    parser.add_argument("--selected-json", type=Path, help="Where to write the selected candidate metadata JSON.")
    parser.add_argument("--report", type=Path, help="Where to write the restock summary report.")
    parser.add_argument("--dry-run", action="store_true", help="Print the decision and selected candidates without calling the downloader.")
    args = parser.parse_args()

    if args.refill_count < 1:
        raise SystemExit("--refill-count must be positive.")

    target_dir = args.target_dir or (ROOT / "library" / "pdfs" / args.project)
    target_dir.mkdir(parents=True, exist_ok=True)

    candidates, profile, profile_path, rows, _ = select_candidates(
        project=args.project,
        topic=args.topic,
        stage=args.stage,
        current_date=args.date,
        refill_count=args.refill_count,
        target_dir=target_dir,
        profile_path=args.profile,
    )
    current_count = local_fulltext_count(rows, target_dir)
    selected_rows = build_selected_rows(candidates)

    report = {
        "project": args.project,
        "date": args.date,
        "threshold": args.min_stored,
        "refill_count": args.refill_count,
        "current_fulltext_count": current_count,
        "triggered": current_count < args.min_stored,
        "profile": str(profile_path),
        "profile_topic": profile.get("topic", ""),
        "stage": daily.auto_stage(profile, daily.load_state(args.project)[0], args.date) if args.stage == "auto" else args.stage,
        "selected_candidates": [
            {
                "citekey": candidate.citekey,
                "title": candidate.title,
                "score": round(candidate.score, 2),
                "reasons": candidate.reasons[:6],
                "detail_url": candidate.meta.get("detail_url", ""),
            }
            for candidate in candidates
        ],
    }

    if not report["triggered"]:
        report["status"] = "threshold_satisfied"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if not selected_rows:
        report["status"] = "no_candidates"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    selected_json = args.selected_json or default_export_path(args.project, "cnki_restock_candidates")
    selected_json.parent.mkdir(parents=True, exist_ok=True)
    selected_json.write_text(json.dumps({"rows": selected_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["selected_json"] = str(selected_json)

    if args.dry_run:
        report["status"] = "dry_run"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    cmd = restock_command(selected_json, args.project, current_count, len(selected_rows), target_dir, args)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    batch_summary = {}
    if stdout:
        try:
            batch_summary = json.loads(stdout)
        except json.JSONDecodeError:
            batch_summary = {"raw_stdout": stdout}
    if stderr:
        batch_summary["stderr"] = stderr

    refreshed_rows = daily.load_matrix(daily.MATRIX, args.project)
    ending_count = local_fulltext_count(refreshed_rows, target_dir)

    report.update(
        {
            "status": "download_run_finished" if proc.returncode == 0 else "download_run_needs_attention",
            "downloader_exit_code": proc.returncode,
            "batch_summary": batch_summary,
            "ending_fulltext_count": ending_count,
        }
    )

    report_path = args.report or default_export_path(args.project, "cnki_restock_report")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
