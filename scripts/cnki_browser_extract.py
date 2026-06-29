#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


JS_EXTRACT_RESULTS = r"""
(() => {
  const clean = (value) => String(value || "").replace(/\s+/g, " ").trim();
  const rows = [...document.querySelectorAll("table tbody tr")].map((tr, idx) => {
    const cells = [...tr.children].map(td => clean(td.innerText));
    const links = [...tr.querySelectorAll("a")];
    const titleLink = links.find(a => String(a.className || "").includes("fz14")) || links[0] || null;
    const downloadLink = links.find(a => String(a.className || "").includes("downloadlink")) ||
      links.find(a => /下载/.test((a.innerText || "") + (a.title || "")) && String(a.href || "").includes("download")) || null;
    const htmlLink = links.find(a => String(a.className || "").includes("icon-html")) ||
      links.find(a => /HTML阅读|原版阅读/.test((a.innerText || "") + (a.title || ""))) || null;
    const aiLink = links.find(a => String(a.className || "").includes("icon-airead")) ||
      links.find(a => /CNKI AI阅读/.test((a.innerText || "") + (a.title || ""))) || null;
    if (!titleLink || cells.length < 7) return null;
    return {
      rank: clean(cells[0]) || String(idx + 1),
      title: clean(cells[1]) || clean(titleLink.innerText),
      authors: clean(cells[2]),
      source: clean(cells[3]),
      published_at: clean(cells[4]),
      publication_type: clean(cells[5]),
      cited_count: clean(cells[6]),
      download_count: clean(cells[7]),
      detail_url: titleLink ? titleLink.href : "",
      download_url: downloadLink ? downloadLink.href : "",
      html_url: htmlLink ? htmlLink.href : "",
      ai_read_url: aiLink ? aiLink.href : ""
    };
  }).filter(Boolean);
  return JSON.stringify({
    title: document.title,
    url: location.href,
    extracted_at: new Date().toISOString(),
    rows
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
    parser = argparse.ArgumentParser(description="Extract the current Chrome CNKI result table to CSV/JSON.")
    parser.add_argument("--csv", required=True, help="Output CSV path")
    parser.add_argument("--json", required=True, help="Output JSON path")
    parser.add_argument("--tag", default="", help="Project tag to include in output")
    args = parser.parse_args()

    data = json.loads(run_chrome_js(JS_EXTRACT_RESULTS))
    rows = data.get("rows", [])

    csv_path = ROOT / args.csv if not Path(args.csv).is_absolute() else Path(args.csv)
    json_path = ROOT / args.json if not Path(args.json).is_absolute() else Path(args.json)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "题名",
        "作者",
        "来源",
        "发表时间",
        "文献类型",
        "被引",
        "下载",
        "详情链接",
        "下载链接",
        "HTML链接",
        "AI阅读链接",
        "项目标签",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "题名": row.get("title", ""),
                    "作者": row.get("authors", ""),
                    "来源": row.get("source", ""),
                    "发表时间": row.get("published_at", ""),
                    "文献类型": row.get("publication_type", ""),
                    "被引": row.get("cited_count", ""),
                    "下载": row.get("download_count", ""),
                    "详情链接": row.get("detail_url", ""),
                    "下载链接": row.get("download_url", ""),
                    "HTML链接": row.get("html_url", ""),
                    "AI阅读链接": row.get("ai_read_url", ""),
                    "项目标签": args.tag,
                }
            )

    print(f"Wrote CSV: {csv_path}")
    print(f"Wrote JSON: {json_path}")
    print(f"Rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
