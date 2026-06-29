#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def run_chrome_js(script: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        js_path = fh.name
    try:
        proc = subprocess.run(
            [
                "osascript",
                "-e",
                f'set jsCode to read POSIX file "{js_path}"',
                "-e",
                'tell application "Google Chrome" to execute active tab of front window javascript jsCode',
            ],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            return "ERR: " + (proc.stderr.strip() or proc.stdout.strip())
        return proc.stdout.strip()
    finally:
        Path(js_path).unlink(missing_ok=True)


PROBES = {
    "title_string": 'JSON.stringify({title: document.title})',
    "iife_basic": '(function() { return JSON.stringify({title: document.title}); })()',
    "query_literal": '(function() { var q = "图书馆 * 短视频"; return JSON.stringify({q:q}); })()',
    "event_new": '(function() { var e = new Event("input", {bubbles: true}); return JSON.stringify({ok: !!e}); })()',
    "selector": '(function() { var b = document.querySelector(".btn-search"); return JSON.stringify({ok: !!b}); })()',
    "extract_shape": r'''(() => {
  const clean = (value) => String(value || "").replace(/\s+/g, " ").trim();
  const rows = [...document.querySelectorAll("table tbody tr")].map((tr, idx) => {
    const cells = [...tr.children].map(td => clean(td.innerText));
    return {rank: String(idx + 1), cells};
  });
  return JSON.stringify({title: document.title, rows});
})()''',
}


def main() -> int:
    results = {}
    for name, script in PROBES.items():
        results[name] = run_chrome_js(script)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
