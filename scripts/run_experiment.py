#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a user-specified experiment command and record logs.")
    parser.add_argument("--project", required=True, help="Project slug")
    parser.add_argument("--name", required=True, help="Run name")
    parser.add_argument("--timeout-min", type=float, default=None)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("Provide a command after --")

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(f"Project not found: {project}")

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in args.name)
    run_dir = project / "passport" / "runs" / f"{stamp}_{safe_name}"
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "project": args.project,
        "name": args.name,
        "command": command,
        "cwd": str(project),
        "started_at": dt.datetime.now().isoformat(timespec="seconds"),
        "timeout_min": args.timeout_min,
    }
    (run_dir / "command.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    environment = {
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "command_executable": command[0],
        "command_resolved_path": shutil.which(command[0]),
    }
    (run_dir / "environment.json").write_text(json.dumps(environment, indent=2, ensure_ascii=False), encoding="utf-8")

    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    print(f"Running in {project}: {' '.join(command)}")
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        try:
            result = subprocess.run(
                command,
                cwd=project,
                stdout=stdout,
                stderr=stderr,
                text=True,
                timeout=args.timeout_min * 60 if args.timeout_min else None,
                check=False,
            )
            return_code = result.returncode
            status = "completed" if return_code == 0 else "failed"
        except subprocess.TimeoutExpired:
            return_code = 124
            status = "timeout"

    finished_at = dt.datetime.now().isoformat(timespec="seconds")
    report = {
        **metadata,
        "finished_at": finished_at,
        "return_code": return_code,
        "status": status,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    (run_dir / "run_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "run_report.md").write_text(
        "\n".join(
            [
                "# Experiment Run Report",
                "",
                f"- Project: {args.project}",
                f"- Name: {args.name}",
                f"- Status: {status}",
                f"- Return code: {return_code}",
                f"- Started: {metadata['started_at']}",
                f"- Finished: {finished_at}",
                f"- Command: `{' '.join(command)}`",
                f"- Environment: `{run_dir / 'environment.json'}`",
                f"- stdout: `{stdout_path}`",
                f"- stderr: `{stderr_path}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Run status: {status}")
    print(f"Run report: {run_dir / 'run_report.md'}")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
