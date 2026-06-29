#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"


JS_EXTRACT = r"""
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


def run_osascript(lines: list[str]) -> str:
    cmd: list[str] = ["osascript"]
    for line in lines:
        cmd.extend(["-e", line])
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def run_chrome_js(script: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        js_path = fh.name
    try:
        return run_osascript(
            [
                f'set jsCode to read POSIX file "{js_path}"',
                'tell application "Google Chrome" to execute active tab of front window javascript jsCode',
            ]
        )
    finally:
        Path(js_path).unlink(missing_ok=True)


def open_url_in_tab(url: str, tab_index: int) -> None:
    run_osascript(
        [
            'tell application "Google Chrome"',
            f"if (count of tabs of front window) < {tab_index} then",
            f'make new tab at end of tabs of front window with properties {{URL:"about:blank"}}',
            "end if",
            f"set active tab index of front window to {tab_index}",
            f'set URL of active tab of front window to "{url}"',
            "activate",
            "end tell",
        ]
    )


def wait_for_reader(min_chars: int, timeout: int) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        time.sleep(2)
        try:
            data = json.loads(run_chrome_js(JS_EXTRACT))
        except Exception:
            continue
        last = data
        if data.get("text_length", 0) >= min_chars and "HTML阅读" in data.get("title", ""):
            return data
    return last


def load_matrix() -> list[dict[str, str]]:
    with MATRIX.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def title_to_citekey(rows: list[dict[str, str]], title: str) -> str:
    matches = [row for row in rows if title in row.get("title", "") or row.get("title", "") in title]
    if not matches:
        raise KeyError(f"No citekey found for title: {title}")
    if len(matches) > 1:
        exact = [row for row in matches if row.get("title", "") == title]
        if len(exact) == 1:
            return exact[0]["citekey"]
    return matches[0]["citekey"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Open CNKI HTML links and build deterministic reader packages.")
    parser.add_argument("--export-json", required=True, help="JSON from cnki_browser_extract.py")
    parser.add_argument("--project", required=True)
    parser.add_argument("--titles-file", required=True, help="UTF-8 text file, one title per line")
    parser.add_argument("--tab-index", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--min-chars", type=int, default=1000)
    args = parser.parse_args()

    export_path = ROOT / args.export_json if not Path(args.export_json).is_absolute() else Path(args.export_json)
    titles_path = ROOT / args.titles_file if not Path(args.titles_file).is_absolute() else Path(args.titles_file)
    export = json.loads(export_path.read_text(encoding="utf-8"))
    rows = export.get("rows", [])
    matrix_rows = load_matrix()
    wanted_titles = [line.strip() for line in titles_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    built = []
    missing = []
    for wanted in wanted_titles:
        row = next((item for item in rows if wanted in item.get("title", "")), None)
        if not row or not row.get("html_url"):
            missing.append(wanted)
            continue
        citekey = title_to_citekey(matrix_rows, row["title"])
        open_url_in_tab(row["html_url"], args.tab_index)
        data = wait_for_reader(args.min_chars, args.timeout)
        if data.get("text_length", 0) < args.min_chars:
            missing.append(wanted)
            continue

        text_path = ROOT / "library" / "text" / args.project / f"{citekey}.txt"
        meta_path = ROOT / "library" / "text" / args.project / f"{citekey}.json"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(data.get("text", ""), encoding="utf-8")
        meta_path.write_text(json.dumps({k: v for k, v in data.items() if k != "text"}, ensure_ascii=False, indent=2), encoding="utf-8")

        subprocess.run(
            [
                str(ROOT / ".." / "anaconda3" / "bin" / "python"),
                str(ROOT / "scripts" / "paper_reader.py"),
                "--project",
                args.project,
                "--citekey",
                citekey,
                "--text",
                str(text_path),
                "--update-matrix",
            ],
            check=True,
        )
        built.append({"citekey": citekey, "title": row["title"], "text_path": str(text_path), "text_length": data.get("text_length", 0)})

    print(json.dumps({"built": built, "missing": missing}, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
