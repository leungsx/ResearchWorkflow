#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"


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


def resolve_project_path(project: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else project / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_target(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    if path.is_file():
        return {"path": str(path), "exists": True, "kind": "file", "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if path.is_dir():
        files = sorted(item for item in path.rglob("*") if item.is_file())
        digest = hashlib.sha256()
        manifest: list[dict[str, object]] = []
        for item in files:
            rel = item.relative_to(path).as_posix()
            item_hash = sha256_file(item)
            digest.update(rel.encode("utf-8"))
            digest.update(item_hash.encode("ascii"))
            manifest.append({"path": rel, "bytes": item.stat().st_size, "sha256": item_hash})
        return {"path": str(path), "exists": True, "kind": "directory", "file_count": len(files), "sha256": digest.hexdigest(), "files": manifest}
    return {"path": str(path), "exists": True, "kind": "other"}


def write_pip_freeze(run_dir: Path) -> str:
    output = run_dir / "pip_freeze.txt"
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        output.write_text(result.stdout, encoding="utf-8")
        return str(output)
    output.write_text(result.stderr, encoding="utf-8")
    return str(output)


def snapshot_params(project: Path, run_dir: Path, raw_paths: list[str]) -> list[dict[str, object]]:
    snapshots: list[dict[str, object]] = []
    if not raw_paths:
        return snapshots
    target_dir = run_dir / "params"
    target_dir.mkdir(exist_ok=True)
    for raw_path in raw_paths:
        source = resolve_project_path(project, raw_path)
        record = hash_target(source)
        if source.exists() and source.is_file():
            destination = target_dir / source.name
            shutil.copy2(source, destination)
            record["snapshot_path"] = str(destination)
        snapshots.append(record)
    return snapshots


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a user-specified experiment command and record logs.")
    parser.add_argument("--project", required=True, help="Project slug")
    parser.add_argument("--name", required=True, help="Run name")
    parser.add_argument("--hypothesis-id", default="", help="Optional hypothesis ID linked to this run.")
    parser.add_argument("--seed", default="", help="Random seed used by the experiment, if any.")
    parser.add_argument("--inputs", nargs="*", default=[], help="Project-relative or absolute input files/directories to hash before the run.")
    parser.add_argument("--outputs", nargs="*", default=[], help="Project-relative or absolute output files/directories to hash after the run.")
    parser.add_argument("--params", nargs="*", default=[], help="Project-relative or absolute parameter files to snapshot.")
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
    run_id = run_dir.name
    input_paths = [resolve_project_path(project, item) for item in args.inputs]
    output_paths = [resolve_project_path(project, item) for item in args.outputs]
    missing_inputs = [str(path) for path in input_paths if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError("Missing experiment input(s): " + "; ".join(missing_inputs))

    metadata = {
        "run_id": run_id,
        "project": args.project,
        "name": args.name,
        "hypothesis_id": args.hypothesis_id,
        "random_seed": args.seed,
        "command": command,
        "cwd": str(project),
        "started_at": dt.datetime.now().isoformat(timespec="seconds"),
        "timeout_min": args.timeout_min,
        "git_commit": git_commit(),
    }
    (run_dir / "command.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    input_hashes = [hash_target(path) for path in input_paths]
    (run_dir / "inputs.json").write_text(json.dumps(input_hashes, indent=2, ensure_ascii=False), encoding="utf-8")
    param_snapshots = snapshot_params(project, run_dir, args.params)

    environment = {
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "command_executable": command[0],
        "command_resolved_path": shutil.which(command[0]),
        "pip_freeze": write_pip_freeze(run_dir),
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
    output_hashes = [hash_target(path) for path in output_paths]
    (run_dir / "outputs.json").write_text(json.dumps(output_hashes, indent=2, ensure_ascii=False), encoding="utf-8")
    report = {
        **metadata,
        "finished_at": finished_at,
        "return_code": return_code,
        "status": status,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "input_files": input_hashes,
        "output_files": output_hashes,
        "parameter_snapshots": param_snapshots,
        "environment_lock": environment["pip_freeze"],
    }
    (run_dir / "run_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "run_report.md").write_text(
        "\n".join(
            [
                "# Experiment Run Report",
                "",
                f"- Project: {args.project}",
                f"- Name: {args.name}",
                f"- Run ID: `{run_id}`",
                f"- Hypothesis ID: `{args.hypothesis_id or 'not set'}`",
                f"- Status: {status}",
                f"- Return code: {return_code}",
                f"- Started: {metadata['started_at']}",
                f"- Finished: {finished_at}",
                f"- Git commit: `{metadata['git_commit'] or 'unknown'}`",
                f"- Random seed: `{args.seed or 'not set'}`",
                f"- Command: `{' '.join(command)}`",
                f"- Inputs: `{run_dir / 'inputs.json'}`",
                f"- Outputs: `{run_dir / 'outputs.json'}`",
                f"- Environment: `{run_dir / 'environment.json'}`",
                f"- Environment lock: `{environment['pip_freeze']}`",
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
