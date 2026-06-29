#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"


def run_osascript(lines: list[str]) -> str:
    cmd: list[str] = ["osascript"]
    for line in lines:
        cmd.extend(["-e", line])
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def ensure_chrome_window() -> None:
    run_osascript(
        [
            'tell application "Google Chrome"',
            "activate",
            "if (count of windows) = 0 then make new window",
            "end tell",
        ]
    )


def run_chrome_js(script: str) -> str:
    ensure_chrome_window()
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


def active_tab_state() -> dict:
    script = """
(() => JSON.stringify({
  ok: true,
  url: location.href,
  title: document.title,
  ready_state: document.readyState,
  body: String(document.body ? document.body.innerText : "").slice(0, 600)
}))()
"""
    return json.loads(run_chrome_js(script))


def sleep_between_attempts(delay_min: float, delay_max: float) -> None:
    if delay_max <= 0:
        return
    lo = max(0.0, delay_min)
    hi = max(lo, delay_max)
    time.sleep(random.uniform(lo, hi))


def confirm_save_dialog_if_present(delay: float) -> str:
    if delay > 0:
        time.sleep(delay)
    return run_osascript(
        [
            'tell application "System Events"',
            'if exists process "Google Chrome" then',
            'tell process "Google Chrome"',
            'if exists window "保存" then',
            'keystroke return',
            'return "confirmed_window"',
            'end if',
            'repeat with w in windows',
            'if exists sheet 1 of w then',
            'keystroke return',
            'return "confirmed_sheet"',
            'end if',
            'end repeat',
            'end tell',
            'end if',
            'return "none"',
            'end tell',
        ]
    )


def navigate_to(url: str, timeout: float = 20.0) -> dict:
    ensure_chrome_window()
    previous_url = ""
    try:
        previous_url = str(active_tab_state().get("url", ""))
    except Exception:
        previous_url = ""
    # Set the Chrome tab URL directly so recovery still works after a PDF viewer
    # or another non-HTML document takes over the active tab.
    run_osascript(
        [
            'tell application "Google Chrome"',
            f"set URL of active tab of front window to {json.dumps(url)}",
            "end tell",
        ]
    )
    deadline = time.time() + timeout
    last: dict = {"ok": False, "reason": "not_ready"}
    while time.time() < deadline:
        try:
            last = active_tab_state()
            current_url = str(last.get("url", ""))
            changed_page = not previous_url or current_url != previous_url or current_url == url
            still_on_blank = current_url.startswith("chrome://new-tab") or current_url.startswith("chrome://newtab")
            still_on_verify = "verify/home" in current_url or str(last.get("title", "")) == "安全验证"
            if last.get("ready_state") in {"interactive", "complete"} and changed_page and not still_on_blank and not still_on_verify:
                return last
        except Exception as exc:  # Browser may be between pages.
            last = {"ok": False, "reason": str(exc)}
        time.sleep(0.5)
    return last


def find_detail_link(title: str) -> dict:
    script = f"""
(() => {{
  const target = {json.dumps(title, ensure_ascii=True)};
  const clean = value => String(value || "").replace(/\\s+/g, " ").trim();
  const links = [...document.querySelectorAll("a")]
    .filter(a => clean(a.innerText).includes(target) || clean(a.title).includes(target));
  const article = links.find(a => /\\/kcms2\\/article\\/abstract|\\/kcms\\/detail|kns\\.cnki\\.net/i.test(a.href || "")) || links[0] || null;
  if (!article) {{
    return JSON.stringify({{
      ok: false,
      reason: "detail_link_not_found",
      url: location.href,
      title: document.title,
      body_has_target: document.body.innerText.includes(target),
      sample_links: [...document.querySelectorAll("a")].map(a => clean(a.innerText || a.title)).filter(Boolean).slice(0, 30)
    }});
  }}
  return JSON.stringify({{ok: true, href: article.href, text: clean(article.innerText || article.title), url: location.href}});
}})()
"""
    return json.loads(run_chrome_js(script))


def click_detail_pdf_download() -> dict:
    script = r"""
(() => {
  const clean = value => String(value || "").replace(/\s+/g, " ").trim();
  const pageText = clean([document.title, location.href, document.body ? document.body.innerText : ""].join(" "));
  let barrier = "";
  if (/verify\/home|拖动下方拼图|安全验证|验证码|滑块|拼图验证/i.test(pageText)) barrier = "captcha";
  if (/未订购|个人账号下载阅读|没有权限|暂无权限|机构未订购/i.test(pageText)) barrier = barrier || "subscription_or_permission";
  if (/高校\/机构外部访问系统|高校\/机构:|机构登录|个人登录/i.test(pageText) && !/PDF下载/i.test(pageText)) barrier = barrier || "login_or_institution";
  if (barrier) {
    return JSON.stringify({
      ok: false,
      reason: "access_barrier",
      barrier,
      url: location.href,
      title: document.title,
      body: pageText.slice(0, 600)
    });
  }
  const nodes = [];
  const allCandidates = [];
  [...document.querySelectorAll("a, button")].forEach((el, idx) => {
    const rawText = clean([el.innerText, el.title, el.getAttribute("aria-label")].join(" "));
    const href = String(el.href || "");
    const text = clean([rawText, el.id, el.className, href].join(" "));
    const pdf = /\bpdf\b/i.test(text);
    const download = /下载|download|down/i.test(text);
    const bad = /\bcaj\b|kdh|nh|html|xml|AI阅读|广告|ad-item|but-ad|recommend|related/i.test(text) ||
      /\/ads\/|\/pdf\/ads\/|a\.cnki\.net\/gw\/api\/get\/pdf\/ads/i.test(href);
    let score = 0;
    if (/pdf\s*下载|下载\s*pdf|PDF下载/i.test(rawText)) score += 180;
    if (/pdf\s*下载|下载\s*pdf|PDF下载/i.test(text)) score += 80;
    if (/下载|download|down/i.test(rawText)) score += 35;
    if (pdf) score += 25;
    if (download) score += 15;
    if (/download|pdf/i.test(href) && /cnki|kns|oversea|epub|bar\.cnki/i.test(href)) score += 20;
    if (/pdf/i.test(String(el.id || "") + " " + String(el.className || ""))) score += 15;
    if (bad) score -= 500;
    const item = {el, idx, rawText, text, href, score};
    if (/PDF|pdf|下载|download|caj|html|阅读|ads|ad-item|but-ad/i.test(text)) allCandidates.push(item);
    if (score >= 60) nodes.push(item);
  });
  nodes.sort((a, b) => b.score - a.score || a.idx - b.idx);
  const chosen = nodes[0];
  if (!chosen) {
    allCandidates.sort((a, b) => b.score - a.score || a.idx - b.idx);
    return JSON.stringify({
      ok: false,
      reason: "pdf_download_link_not_found",
      url: location.href,
      title: document.title,
      candidates: allCandidates.slice(0, 12).map(item => ({rawText: item.rawText, text: item.text, href: item.href, score: item.score}))
    });
  }
  chosen.el.scrollIntoView({block: "center", inline: "center"});
  chosen.el.focus();
  chosen.el.click();
  return JSON.stringify({ok: true, mode: "detail_pdf", page_title: document.title, page_url: location.href, href: chosen.href, rawText: chosen.rawText, text: chosen.text, score: chosen.score});
})()
"""
    return json.loads(run_chrome_js(script))


def wait_and_click_detail_pdf_download(timeout: float) -> dict:
    deadline = time.time() + timeout
    last: dict = {"ok": False, "reason": "not_attempted"}
    while time.time() < deadline:
        last = click_detail_pdf_download()
        if last.get("ok"):
            return last
        if last.get("reason") == "access_barrier":
            return last
        time.sleep(0.75)
    return last


def click_result_download(title: str) -> dict:
    script = f"""
(() => {{
  const target = {json.dumps(title, ensure_ascii=True)};
  const clean = value => String(value || "").replace(/\\s+/g, " ").trim();
  const pageText = clean([document.title, location.href, document.body ? document.body.innerText : ""].join(" "));
  let barrier = "";
  if (/verify\/home|拖动下方拼图|安全验证|验证码|滑块|拼图验证/i.test(pageText)) barrier = "captcha";
  if (/未订购|个人账号下载阅读|没有权限|暂无权限|机构未订购/i.test(pageText)) barrier = barrier || "subscription_or_permission";
  if (/高校\\/机构外部访问系统|高校\\/机构:|机构登录|个人登录/i.test(pageText) && !/下载/i.test(pageText)) barrier = barrier || "login_or_institution";
  if (barrier) {{
    return JSON.stringify({{
      ok: false,
      reason: "access_barrier",
      barrier,
      url: location.href,
      title: document.title,
      body: pageText.slice(0, 600)
    }});
  }}
  const downloadWord = "\\u4e0b\\u8f7d";
  const row = [...document.querySelectorAll("table tbody tr, tr, li, dl, div")]
    .filter(el => (el.innerText || "").includes(target))
    .filter(el => [...el.querySelectorAll("a")].some(a => String(a.className || "").includes("downloadlink") || ((a.innerText || "") + (a.title || "")).includes(downloadWord)))
    .sort((a, b) => (a.innerText || "").length - (b.innerText || "").length)[0];
  if (!row) {{
    return JSON.stringify({{
      ok: false,
      reason: "row_not_found",
      url: location.href,
      title: document.title,
      body_has_target: document.body.innerText.includes(target),
      body: document.body.innerText.slice(0, 600)
    }});
  }}
  const link = [...row.querySelectorAll("a")].find(a => String(a.className || "").includes("downloadlink")) ||
    [...row.querySelectorAll("a")].find(a => ((a.innerText || "") + (a.title || "")).includes(downloadWord));
  if (!link) return JSON.stringify({{ok: false, reason: "download_not_found", row: row.innerText.slice(0, 600)}});
  link.scrollIntoView({{block: "center", inline: "center"}});
  link.focus();
  link.click();
  return JSON.stringify({{ok: true, page_title: document.title, page_url: location.href, href: link.href}});
}})()
"""
    return json.loads(run_chrome_js(script))


def trigger_download(title: str, mode: str, result_url: str, detail_timeout: float) -> dict:
    if mode in {"detail-pdf-first", "detail-pdf-only"}:
        detail = find_detail_link(title)
        if detail.get("ok"):
            navigate_to(detail["href"], timeout=detail_timeout)
            clicked = wait_and_click_detail_pdf_download(timeout=detail_timeout)
            if clicked.get("ok"):
                clicked["detail_url"] = detail["href"]
                return clicked
            if result_url:
                navigate_to(result_url, timeout=detail_timeout)
            if mode == "detail-pdf-only":
                clicked["detail_url"] = detail["href"]
                return clicked
        elif mode == "detail-pdf-only":
            return detail

    if result_url:
        navigate_to(result_url, timeout=detail_timeout)
    clicked = click_result_download(title)
    if clicked.get("ok"):
        clicked["mode"] = "result_direct"
    return clicked


def finder_download_names() -> list[str]:
    out = run_osascript(
        [
            'tell application "Finder"',
            'set outText to ""',
            'repeat with f in files of folder "Downloads" of home',
            'set outText to outText & (name of f as text) & linefeed',
            "end repeat",
            "return outText",
            "end tell",
        ]
    )
    return [line for line in out.splitlines() if line.strip()]


def recent_download_candidates(started_at: float) -> list[str]:
    # macOS privacy controls may deny Python direct access to ~/Downloads even
    # when Finder can list authorized user files. Keep the recency check in
    # Finder so the workflow works with ordinary Chrome downloads.
    lookback_seconds = max(5, int(time.time() - started_at) + 5)
    out = run_osascript(
        [
            'tell application "Finder"',
            f"set cutoffDate to (current date) - {lookback_seconds}",
            'set outText to ""',
            'repeat with f in files of folder "Downloads" of home',
            'set fileName to name of f as text',
            'if modification date of f is greater than cutoffDate then',
            'set outText to outText & fileName & linefeed',
            "end if",
            "end repeat",
            "return outText",
            "end tell",
        ]
    )
    candidates = [
        line
        for line in out.splitlines()
        if Path(line).suffix.lower() in {".caj", ".pdf", ".nh"} and not line.endswith(".crdownload")
    ]
    return candidates


def find_downloaded_file(title: str, timeout: float, started_at: float) -> str | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        names = finder_download_names()
        matches = [
            name
            for name in names
            if title in name
            and not name.endswith(".crdownload")
            and Path(name).suffix.lower() in {".caj", ".pdf", ".nh"}
        ]
        if matches:
            return sorted(matches, key=len)[0]
        recent = recent_download_candidates(started_at)
        if len(recent) == 1:
            return recent[0]
        time.sleep(1.0)
    return None


def finder_duplicate_to_project(source_name: str, target_dir: Path, target_name: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / target_name
    if target_path.exists():
        return target_path
    run_osascript(
        [
            'tell application "Finder"',
            f'set destFolder to POSIX file "{target_dir}/" as alias',
            f"set srcFile to file {json.dumps(source_name)} of folder \"Downloads\" of home",
            "set copiedFile to duplicate srcFile to destFolder with replacing",
            f"set name of copiedFile to {json.dumps(target_name)}",
            "return name of copiedFile",
            "end tell",
        ]
    )
    return target_path


def load_matrix() -> tuple[list[dict], list[str]]:
    with MATRIX.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_matrix(rows: list[dict], fieldnames: list[str]) -> None:
    with MATRIX.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def citekey_for_title(rows: list[dict], title: str) -> str:
    matches = [row["citekey"] for row in rows if row.get("title") == title]
    if not matches:
        raise ValueError(f"Title not found in literature matrix: {title}")
    return matches[0]


def update_pdf_path(rows: list[dict], citekey: str, path: Path) -> None:
    for row in rows:
        if row.get("citekey") == citekey:
            row["pdf_path"] = str(path)
            return
    raise ValueError(f"Citekey not found in literature matrix: {citekey}")


def should_skip_existing(existing: list[Path], mode: str) -> Path | None:
    pdfs = [path for path in existing if path.suffix.lower() == ".pdf"]
    if pdfs:
        return pdfs[0]
    if mode == "result-direct" and existing:
        return existing[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Click CNKI download links for titles on the current result page.")
    parser.add_argument("--title", action="append", default=[], help="Exact title to download; can be repeated")
    parser.add_argument("--titles-file", type=Path, help="One exact title per line")
    parser.add_argument("--target-dir", type=Path, default=ROOT / "library" / "pdfs" / "library_short_video")
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--detail-timeout", type=float, default=20)
    parser.add_argument(
        "--download-mode",
        choices=["detail-pdf-first", "detail-pdf-only", "result-direct"],
        default="detail-pdf-first",
        help="Prefer CNKI detail-page PDF download; fall back to result-row download unless detail-pdf-only is used.",
    )
    parser.add_argument("--delay-min", type=float, default=20.0, help="Minimum seconds to wait between titles.")
    parser.add_argument("--delay-max", type=float, default=35.0, help="Maximum seconds to wait between titles.")
    parser.add_argument("--no-stop-on-barrier", action="store_true", help="Continue after CAPTCHA/login/permission barriers instead of stopping this run.")
    parser.add_argument("--confirm-save-dialog", action="store_true", help="If a macOS Chrome save dialog appears after clicking download, press Return to save to the current folder.")
    parser.add_argument("--save-dialog-delay", type=float, default=1.2, help="Seconds to wait before checking for a save dialog.")
    parser.add_argument("--update-matrix", action="store_true")
    args = parser.parse_args()

    titles = list(args.title)
    if args.titles_file:
        titles.extend(
            line.strip()
            for line in args.titles_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    seen: set[str] = set()
    titles = [title for title in titles if not (title in seen or seen.add(title))]
    if not titles:
        raise SystemExit("No titles provided.")

    rows, fieldnames = load_matrix()
    result_url = active_tab_state().get("url", "")
    results = []
    for title in titles:
        citekey = citekey_for_title(rows, title)
        existing = sorted(args.target_dir.glob(f"{citekey}.*"))
        reusable = should_skip_existing(existing, args.download_mode)
        if reusable:
            if args.update_matrix:
                update_pdf_path(rows, citekey, reusable)
            results.append({"title": title, "citekey": citekey, "status": "already_present", "path": str(reusable)})
            continue
        started_at = time.time()
        stop_after_title = False
        try:
            clicked = trigger_download(title, args.download_mode, result_url, args.detail_timeout)
            if not clicked.get("ok"):
                results.append({"title": title, "citekey": citekey, "status": "click_failed", "detail": clicked})
                if clicked.get("reason") == "access_barrier" and not args.no_stop_on_barrier:
                    stop_after_title = True
                    break
                if result_url:
                    navigate_to(result_url, timeout=args.detail_timeout)
                continue
            if args.confirm_save_dialog:
                clicked["save_dialog"] = confirm_save_dialog_if_present(args.save_dialog_delay)
            source_name = find_downloaded_file(title, args.timeout, started_at)
            if not source_name:
                results.append({"title": title, "citekey": citekey, "status": "download_not_found", "detail": clicked})
                continue
            suffix = Path(source_name).suffix.lower()
            target_path = finder_duplicate_to_project(source_name, args.target_dir, f"{citekey}{suffix}")
            if args.update_matrix:
                update_pdf_path(rows, citekey, target_path)
            results.append({"title": title, "citekey": citekey, "status": "copied", "source": source_name, "path": str(target_path)})
            if result_url:
                navigate_to(result_url, timeout=args.detail_timeout)
        finally:
            if not stop_after_title and title != titles[-1]:
                sleep_between_attempts(args.delay_min, args.delay_max)

    if args.update_matrix:
        write_matrix(rows, fieldnames)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    failed = [item for item in results if item["status"] in {"click_failed", "download_not_found"}]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
