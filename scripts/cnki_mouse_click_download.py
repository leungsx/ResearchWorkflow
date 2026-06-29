#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path


JS_TEMPLATE = r"""
(() => {
  const target = TARGET_JSON;
  const candidates = [...document.querySelectorAll("tr, li, dl, div")]
    .filter(el => (el.innerText || "").includes(target));
  let row = candidates
    .filter(el => [...el.querySelectorAll("a")].some(a => String(a.className || "").includes("downloadlink") || /下载/.test((a.innerText || "") + (a.title || ""))))
    .sort((a, b) => (a.innerText || "").length - (b.innerText || "").length)[0];
  let download = null;
  if (row) {
    download = [...row.querySelectorAll("a")].find(a => String(a.className || "").includes("downloadlink")) ||
      [...row.querySelectorAll("a")].find(a => /下载/.test((a.innerText || "") + (a.title || "")));
  }
  if (!row) {
    const titleLinks = [...document.querySelectorAll("a")].filter(a => (a.innerText || "").includes(target));
    const titleLink = titleLinks[0];
    const titleResultLinks = [...document.querySelectorAll("a.fz14")].filter(a => (a.href || "").includes("/kcms2/article/abstract"));
    const titleIndex = titleLink ? titleResultLinks.indexOf(titleLink) : -1;
    const downloads = [...document.querySelectorAll("a.downloadlink")];
    if (titleIndex >= 0 && downloads[titleIndex]) {
      row = titleLink.closest("tr, li, dl, div") || titleLink.parentElement;
      download = downloads[titleIndex];
    }
  }
  if (!row) {
    return JSON.stringify({
      ok: false,
      reason: "row_not_found",
      url: location.href,
      title: document.title,
      body_has_target: document.body.innerText.includes(target),
      candidate_count: candidates.length,
      title_link_count: [...document.querySelectorAll("a")].filter(a => (a.innerText || "").includes(target)).length,
      title_result_link_count: [...document.querySelectorAll("a.fz14, a")].filter(a => (a.href || "").includes("/kcms2/article/abstract")).length,
      downloadlink_count: document.querySelectorAll("a.downloadlink").length,
      sample_links: [...document.querySelectorAll("a")].map(a => (a.innerText || "").trim()).filter(Boolean).slice(0, 30),
      body: document.body.innerText.slice(0, 800)
    });
  }
  if (!download) {
    return JSON.stringify({ok: false, reason: "download_not_found", row: row.innerText.slice(0, 800)});
  }
  download.scrollIntoView({block: "center", inline: "center"});
  const rect = download.getBoundingClientRect();
  return JSON.stringify({
    ok: true,
    page_title: document.title,
    page_url: location.href,
    row_title: (row.children[1] && row.children[1].innerText || "").trim(),
    href: download.href,
    rect: {left: rect.left, top: rect.top, width: rect.width, height: rect.height},
    screen: {
      x: window.screenX,
      y: window.screenY,
      outerWidth: window.outerWidth,
      outerHeight: window.outerHeight,
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      devicePixelRatio: window.devicePixelRatio
    }
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Mouse-click a CNKI download button by matching result title.")
    parser.add_argument("--title", required=True, help="Unique title substring to match in the current CNKI result page")
    parser.add_argument("--x-offset", type=int, default=0, help="Manual x calibration in screen pixels")
    parser.add_argument("--y-offset", type=int, default=0, help="Manual y calibration in screen pixels")
    parser.add_argument("--dry-run", action="store_true", help="Only print coordinates; do not click")
    parser.add_argument("--wait", type=float, default=0.5)
    args = parser.parse_args()

    script = JS_TEMPLATE.replace("TARGET_JSON", json.dumps(args.title))
    info = json.loads(run_chrome_js(script))
    if not info.get("ok"):
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 2

    rect = info["rect"]
    screen = info["screen"]
    x = int(round(screen["x"] + rect["left"] + rect["width"] / 2 + args.x_offset))
    y = int(round(screen["y"] + rect["top"] + rect["height"] / 2 + args.y_offset))
    info["click"] = {"x": x, "y": y, "x_offset": args.x_offset, "y_offset": args.y_offset}
    print(json.dumps(info, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0

    time.sleep(args.wait)
    run_osascript(
        [
            'tell application "Google Chrome" to activate',
            "delay 0.2",
            f'tell application "System Events" to click at {{{x}, {y}}}',
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
