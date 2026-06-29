#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


JS_EXTRACT_READER = r"""
(() => {
  const clean = (value) => String(value || "").replace(/\r/g, "\n").replace(/[ \t]+\n/g, "\n").trim();
  return JSON.stringify({
    title: document.title,
    url: location.href,
    extracted_at: new Date().toISOString(),
    text_length: clean(document.body.innerText).length,
    text: clean(document.body.innerText)
  });
})()
"""


def run_chrome_js(script: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        js_path = fh.name
    osa = [
        "osascript",
        "-e",
        f'set jsCode to read POSIX file "{js_path}"',
        "-e",
        'tell application "Google Chrome" to execute active tab of front window javascript jsCode',
    ]
    proc = subprocess.run(osa, text=True, capture_output=True)
    Path(js_path).unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract current Chrome CNKI HTML reader text.")
    parser.add_argument("--text", required=True, help="Output text path")
    parser.add_argument("--json", required=True, help="Output metadata JSON path")
    args = parser.parse_args()

    data = json.loads(run_chrome_js(JS_EXTRACT_READER))
    text_path = ROOT / args.text if not Path(args.text).is_absolute() else Path(args.text)
    json_path = ROOT / args.json if not Path(args.json).is_absolute() else Path(args.json)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    text_path.write_text(data.get("text", ""), encoding="utf-8")
    json_path.write_text(json.dumps({k: v for k, v in data.items() if k != "text"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote text: {text_path}")
    print(f"Wrote JSON: {json_path}")
    print(f"Title: {data.get('title', '')}")
    print(f"Text length: {data.get('text_length', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
