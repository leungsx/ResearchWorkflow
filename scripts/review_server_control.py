#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABEL = "com.researchworkflow.review-server"
DOMAIN = f"gui/{os.getuid()}"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
TMP = ROOT / ".tmp"


def health(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True)


def write_plist(port: int) -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "Label": LABEL,
        "ProgramArguments": [
            sys.executable,
            str(ROOT / "scripts" / "review_mark_server.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        "WorkingDirectory": str(ROOT),
        "RunAtLoad": True,
        "KeepAlive": False,
        "EnvironmentVariables": {"PYTHONDONTWRITEBYTECODE": "1"},
        "StandardOutPath": str(TMP / "review-server.out.log"),
        "StandardErrorPath": str(TMP / "review-server.err.log"),
    }
    with PLIST.open("wb") as handle:
        plistlib.dump(payload, handle, sort_keys=False)


def print_launch_error(result: subprocess.CompletedProcess[str]) -> None:
    detail = (result.stderr or result.stdout).strip()
    if detail:
        print(detail)


def start(port: int) -> int:
    if health(port):
        print(f"Review server already running at http://127.0.0.1:{port}/health")
        return 0

    write_plist(port)
    run(["launchctl", "bootout", DOMAIN, str(PLIST)])
    result = run(["launchctl", "bootstrap", DOMAIN, str(PLIST)])
    if result.returncode != 0:
        print_launch_error(result)
        return result.returncode
    run(["launchctl", "kickstart", "-k", f"{DOMAIN}/{LABEL}"])

    for _ in range(20):
        if health(port):
            print(f"Review server started at http://127.0.0.1:{port}/health")
            return 0
        time.sleep(0.25)
    print(f"Review server did not become healthy. Check {TMP / 'review-server.err.log'}")
    return 1


def stop(port: int) -> int:
    result = run(["launchctl", "bootout", DOMAIN, str(PLIST)])
    if result.returncode != 0 and health(port):
        print_launch_error(result)
        return result.returncode
    print("Review server stopped.")
    return 0


def status(port: int) -> int:
    if health(port):
        print(f"Review server is running at http://127.0.0.1:{port}/health")
        return 0
    loaded = run(["launchctl", "print", f"{DOMAIN}/{LABEL}"]).returncode == 0
    if loaded:
        print(f"Review server launch agent is loaded, but health check failed on port {port}.")
        return 1
    print("Review server is not running.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the local review writeback server LaunchAgent.")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"])
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.action == "start":
        return start(args.port)
    if args.action == "stop":
        return stop(args.port)
    if args.action == "restart":
        stop(args.port)
        return start(args.port)
    return status(args.port)


if __name__ == "__main__":
    raise SystemExit(main())
