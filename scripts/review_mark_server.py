#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rendering.review import mark_reviewed  # noqa: E402


def parse_day(value: str | None) -> dt.date | None:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def regenerate_views() -> None:
    commands = [
        [sys.executable, "scripts/build_review_state.py"],
        [sys.executable, "scripts/build_learning_dashboard.py"],
        [sys.executable, "scripts/build_workflow_state.py"],
        [sys.executable, "scripts/build_action_queue.py"],
        [sys.executable, "scripts/build_collaboration_state.py"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "ReviewMarkServer/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_json(200, {"ok": True})

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"ok": True, "service": "review-mark"})
            return
        self.send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/review/studied":
            self.send_json(404, {"ok": False, "error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            ids = payload.get("ids")
            if isinstance(payload.get("id"), str):
                ids = [payload["id"]]
            if ids is not None and not isinstance(ids, list):
                raise ValueError("ids must be a list")

            marked = mark_reviewed(
                ids=ids,
                all_due=bool(payload.get("all_due")),
                day=parse_day(payload.get("date")),
                next_days=payload.get("next_days"),
                learning_status=payload.get("status", "learned"),
            )
            regenerate_views()
            self.send_json(
                200,
                {
                    "ok": True,
                    "marked_count": len(marked),
                    "marked": [{"id": row.get("id", ""), "title": row.get("title", "")} for row in marked],
                },
            )
        except Exception as exc:
            self.send_json(500, {"ok": False, "error": str(exc)})


def main() -> int:
    parser = argparse.ArgumentParser(description="Local review queue writeback server for HTML pages.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ReviewHandler)
    print(f"Review mark server running at http://{args.host}:{args.port}/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped review mark server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
