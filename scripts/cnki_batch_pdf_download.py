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
FULLTEXT_SUFFIXES = {".pdf", ".caj", ".nh", ".kdh"}


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


def chrome_state() -> dict:
    script = r"""
(function() {
  return JSON.stringify({
    title: document.title,
    url: location.href,
    ready_state: document.readyState,
    body: String(document.body ? document.body.innerText : "").slice(0, 400)
  });
})()
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


def navigate_to(url: str, timeout: float = 25.0) -> dict:
    ensure_chrome_window()
    previous_url = ""
    try:
        previous_url = str(chrome_state().get("url", ""))
    except Exception:
        previous_url = ""
    # Use Chrome's tab URL property instead of page JavaScript so navigation also
    # works after a PDF viewer or non-HTML page has taken over the active tab.
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
            last = chrome_state()
            current_url = str(last.get("url", ""))
            changed_page = not previous_url or current_url != previous_url or current_url == url
            still_on_blank = current_url.startswith("chrome://new-tab") or current_url.startswith("chrome://newtab")
            still_on_verify = "verify/home" in current_url or str(last.get("title", "")) == "安全验证"
            if last.get("ready_state") in {"interactive", "complete"} and changed_page and not still_on_blank and not still_on_verify:
                last["ok"] = True
                return last
        except Exception as exc:
            last = {"ok": False, "reason": str(exc)}
        time.sleep(0.8)
    return last


def open_direct_url(url: str) -> None:
    ensure_chrome_window()
    run_osascript(
        [
            'tell application "Google Chrome"',
            f"set URL of active tab of front window to {json.dumps(url)}",
            "end tell",
        ]
    )


def click_pdf_download() -> dict:
    script = r"""
(function() {
  function clean(value) { return String(value || "").replace(/\s+/g, " ").trim(); }
  var pageText = clean([document.title, location.href, document.body ? document.body.innerText : ""].join(" "));
  var barrier = "";
  if (/verify\/home|拖动下方拼图|安全验证|验证码|滑块|拼图验证/i.test(pageText)) barrier = "captcha";
  if (/未订购|个人账号下载阅读|没有权限|暂无权限|机构未订购/i.test(pageText)) barrier = barrier || "subscription_or_permission";
  if (/高校\/机构外部访问系统|高校\/机构:|机构登录|个人登录/i.test(pageText) && !/PDF下载/i.test(pageText)) barrier = barrier || "login_or_institution";
  if (barrier) {
    return JSON.stringify({
      ok: false,
      reason: "access_barrier",
      barrier: barrier,
      title: document.title,
      url: location.href,
      body: pageText.slice(0, 600)
    });
  }
  var elements = document.querySelectorAll("a, button");
  var nodes = [];
  for (var i = 0; i < elements.length; i += 1) {
    var el = elements[i];
    var rawText = clean([el.innerText, el.title, el.getAttribute("aria-label")].join(" "));
    var metaText = clean([el.id, el.className, el.href].join(" "));
    var text = clean(rawText + " " + metaText);
    var href = String(el.href || "");
    var pdf = /\bpdf\b/i.test(text);
    var download = /下载|download|down/i.test(text);
    var bad = /\bcaj\b|kdh|nh|html|xml|AI阅读|广告|ad-item|but-ad|recommend|related/i.test(text) ||
      /\/ads\/|\/pdf\/ads\/|a\.cnki\.net\/gw\/api\/get\/pdf\/ads/i.test(href);
    var score = 0;
    if (/pdf\s*下载|下载\s*pdf|PDF下载/i.test(rawText)) score += 180;
    if (/pdf\s*下载|下载\s*pdf|PDF下载/i.test(text)) score += 80;
    if (/下载|download|down/i.test(rawText)) score += 35;
    if (pdf) score += 25;
    if (download) score += 15;
    if (/download|pdf/i.test(href) && /cnki|kns|oversea|epub/i.test(href)) score += 20;
    if (/pdf/i.test(String(el.id || "") + " " + String(el.className || ""))) score += 15;
    if (bad) score -= 500;
    if (score >= 60) nodes.push({el: el, idx: i, rawText: rawText, text: text, href: href, score: score});
  }
  nodes.sort(function(a, b) { return b.score - a.score || a.idx - b.idx; });
  var chosen = nodes[0];
  if (!chosen) {
    var candidates = [];
    for (var c = 0; c < Math.min(nodes.length, 10); c += 1) {
      candidates.push({rawText: nodes[c].rawText, text: nodes[c].text, href: nodes[c].href, score: nodes[c].score});
    }
    return JSON.stringify({
      ok: false,
      reason: "pdf_download_link_not_found",
      title: document.title,
      url: location.href,
      candidates: candidates
    });
  }
  chosen.el.scrollIntoView({block: "center", inline: "center"});
  var rect = chosen.el.getBoundingClientRect();
  chosen.el.focus();
  chosen.el.click();
  return JSON.stringify({
    ok: true,
    page_title: document.title,
    page_url: location.href,
    href: chosen.href,
    rawText: chosen.rawText,
    text: chosen.text,
    score: chosen.score,
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
    return json.loads(run_chrome_js(script))


def click_any_download() -> dict:
    script = r"""
(function() {
  function clean(value) { return String(value || "").replace(/\s+/g, " ").trim(); }
  var pageText = clean([document.title, location.href, document.body ? document.body.innerText : ""].join(" "));
  var barrier = "";
  if (/verify\/home|拖动下方拼图|安全验证|验证码|滑块|拼图验证/i.test(pageText)) barrier = "captcha";
  if (/未订购|个人账号下载阅读|没有权限|暂无权限|机构未订购/i.test(pageText)) barrier = barrier || "subscription_or_permission";
  if (/高校\/机构外部访问系统|高校\/机构:|机构登录|个人登录/i.test(pageText) && !/下载/i.test(pageText)) barrier = barrier || "login_or_institution";
  if (barrier) {
    return JSON.stringify({
      ok: false,
      reason: "access_barrier",
      barrier: barrier,
      title: document.title,
      url: location.href,
      body: pageText.slice(0, 600)
    });
  }
  var elements = document.querySelectorAll("a, button");
  var nodes = [];
  for (var i = 0; i < elements.length; i += 1) {
    var el = elements[i];
    var rawText = clean([el.innerText, el.title, el.getAttribute("aria-label")].join(" "));
    var href = String(el.href || "");
    var text = clean([rawText, el.id, el.className, href].join(" "));
    var mentionsDownload = /下载|download|down|整本/i.test(text);
    var mentionsPdf = /\bpdf\b/i.test(text);
    var mentionsCaj = /\bcaj\b|\bnh\b|\bkdh\b/i.test(text);
    var bad = /\bhtml\b|\bxml\b|AI阅读|在线阅读|广告|ad-item|but-ad|recommend|related/i.test(text) ||
      /\/ads\/|\/pdf\/ads\/|a\.cnki\.net\/gw\/api\/get\/pdf\/ads/i.test(href);
    if (!mentionsDownload && !mentionsPdf && !mentionsCaj) {
      continue;
    }
    var score = 0;
    if (/pdf\s*下载|下载\s*pdf|PDF下载/i.test(rawText)) score += 220;
    if (/caj\s*下载|下载\s*caj|CAJ下载/i.test(rawText)) score += 170;
    if (/整本下载/i.test(rawText)) score += 150;
    if (/下载|download|down/i.test(rawText)) score += 95;
    if (mentionsPdf) score += 40;
    if (mentionsCaj) score += 25;
    if (/download|pdf|caj/i.test(href) && /cnki|kns|oversea|epub|bar\.cnki/i.test(href)) score += 30;
    if (/pdf|caj/i.test(String(el.id || "") + " " + String(el.className || ""))) score += 15;
    if (bad) score -= 600;
    if (score >= 60) {
      nodes.push({el: el, idx: i, rawText: rawText, text: text, href: href, score: score});
    }
  }
  nodes.sort(function(a, b) { return b.score - a.score || a.idx - b.idx; });
  var chosen = nodes[0];
  if (!chosen) {
    return JSON.stringify({
      ok: false,
      reason: "download_link_not_found",
      title: document.title,
      url: location.href,
      candidates: nodes.slice(0, 10).map(function(item) {
        return {rawText: item.rawText, text: item.text, href: item.href, score: item.score};
      })
    });
  }
  chosen.el.scrollIntoView({block: "center", inline: "center"});
  var rect = chosen.el.getBoundingClientRect();
  chosen.el.focus();
  chosen.el.click();
  return JSON.stringify({
    ok: true,
    page_title: document.title,
    page_url: location.href,
    href: chosen.href,
    rawText: chosen.rawText,
    text: chosen.text,
    score: chosen.score,
    mode: "detail_any_download",
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
    return json.loads(run_chrome_js(script))


def click_download(allow_non_pdf_fallback: bool) -> dict:
    clicked = click_pdf_download()
    if clicked.get("ok") or not allow_non_pdf_fallback or clicked.get("reason") == "access_barrier":
        return clicked
    fallback = click_any_download()
    if fallback.get("ok"):
        fallback["fallback_after_pdf_miss"] = True
    return fallback


def mouse_click_download_target(detail: dict) -> str:
    rect = detail.get("rect") or {}
    screen = detail.get("screen") or {}
    left = float(rect.get("left", 0))
    top = float(rect.get("top", 0))
    width = float(rect.get("width", 0))
    height = float(rect.get("height", 0))
    screen_x = float(screen.get("x", 0))
    screen_y = float(screen.get("y", 0))
    x = int(round(screen_x + left + width / 2))
    y = int(round(screen_y + top + height / 2))
    return run_osascript(
        [
            'tell application "Google Chrome" to activate',
            "delay 0.2",
            f'tell application "System Events" to click at {{{x}, {y}}}',
        ]
    )


def normalize_title(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or "\u3400" <= ch <= "\u9fff").lower()


def title_matches_page(expected_title: str, page_title: str, body: str = "") -> bool:
    expected = normalize_title(expected_title)
    haystack = normalize_title(page_title + " " + body[:1000])
    if not expected:
        return False
    if expected in haystack:
        return True
    # CNKI page titles can drop subtitles or punctuation. Require a conservative
    # long prefix match before allowing the click.
    return len(expected) >= 12 and expected[:12] in haystack


def access_barrier_from_state(state: dict) -> str:
    url = str(state.get("url", "") or "")
    text = " ".join(str(state.get(key, "") or "") for key in ("title", "body"))
    if "verify/home" in url or any(term in text for term in ("安全验证", "验证码", "拖动下方拼图", "滑块", "拼图验证")):
        return "captcha"
    if any(term in text for term in ("未订购", "个人账号下载阅读", "没有权限", "暂无权限", "机构未订购")):
        return "subscription_or_permission"
    if any(term in text for term in ("高校/机构外部访问系统", "机构登录")) and "PDF下载" not in text:
        return "login_or_institution"
    return ""


def probe_pdf_candidates() -> dict:
    script = r"""
(function() {
  function clean(value) { return String(value || "").replace(/\s+/g, " ").trim(); }
  var pageText = clean([document.title, location.href, document.body ? document.body.innerText : ""].join(" "));
  var barrier = "";
  if (/verify\/home|拖动下方拼图|安全验证|验证码|滑块|拼图验证/i.test(pageText)) barrier = "captcha";
  if (/未订购|个人账号下载阅读|没有权限|暂无权限|机构未订购/i.test(pageText)) barrier = barrier || "subscription_or_permission";
  if (/高校\/机构外部访问系统|高校\/机构:|机构登录|个人登录/i.test(pageText) && !/PDF下载/i.test(pageText)) barrier = barrier || "login_or_institution";
  var elements = document.querySelectorAll("a, button");
  var candidates = [];
  for (var i = 0; i < elements.length; i += 1) {
    var el = elements[i];
    var rawText = clean([el.innerText, el.title, el.getAttribute("aria-label")].join(" "));
    var href = String(el.href || "");
    var metaText = clean([el.id, el.className, href].join(" "));
    var text = clean(rawText + " " + metaText);
    if (/PDF|pdf|下载|download|caj|html|阅读|ads|ad-item|but-ad/i.test(text)) {
      candidates.push({
        idx: i,
        tag: el.tagName,
        rawText: rawText,
        id: el.id || "",
        className: String(el.className || ""),
        href: href,
        visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
        text: text
      });
    }
  }
  return JSON.stringify({title: document.title, url: location.href, barrier: barrier, body: pageText.slice(0, 600), candidates: candidates.slice(0, 120)});
})()
"""
    return json.loads(run_chrome_js(script))


def finder_recent_downloads(started_at: float, suffixes: set[str]) -> list[str]:
    lookback_seconds = max(8, int(time.time() - started_at) + 8)
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
    names = [line.strip() for line in out.splitlines() if line.strip()]
    return [
        name
        for name in names
        if Path(name).suffix.lower() in suffixes and not name.endswith(".crdownload")
    ]


def wait_for_download(title: str, started_at: float, timeout: float, suffixes: set[str]) -> str | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        recent = finder_recent_downloads(started_at, suffixes=suffixes)
        title_matches = [name for name in recent if title and title[:12] in name]
        if title_matches:
            return sorted(title_matches, key=len)[0]
        if len(recent) == 1:
            return recent[0]
        if recent:
            pdfs = [name for name in recent if Path(name).suffix.lower() == ".pdf"]
            if len(pdfs) == 1:
                return pdfs[0]
        time.sleep(1.2)
    return None


def finder_duplicate_to_project(source_name: str, target_dir: Path, target_name: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / target_name
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


def load_export_rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "rows" in data:
        return list(data["rows"])
    if isinstance(data, dict) and "meta" in data and "rows" in data:
        return list(data["rows"])
    raise ValueError(f"Unsupported CNKI JSON format: {path}")


def load_profile(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def row_profile_text(export_row: dict, matrix_row: dict) -> str:
    keys = (
        "title",
        "题名",
        "keywords",
        "关键词",
        "abstract",
        "摘要",
        "core_findings",
        "notes",
    )
    values: list[str] = []
    for row in (export_row, matrix_row):
        for key in keys:
            value = str(row.get(key, "") or "").strip()
            if value:
                values.append(value)
    return " ".join(values)


def matches_profile(export_row: dict, matrix_row: dict, profile: dict) -> bool:
    if not profile:
        return True
    text = row_profile_text(export_row, matrix_row)
    for term in profile.get("exclude_terms", []) or []:
        if term and term in text:
            return False
    groups = profile.get("required_term_groups", []) or []
    for group in groups:
        terms = [str(term) for term in group if str(term)]
        if terms and not any(term in text for term in terms):
            return False
    return True


def title_year(row: dict) -> tuple[str, str]:
    year = ""
    for key in ("published_at", "发表时间", "year"):
        value = str(row.get(key, "") or "")
        if len(value) >= 4 and value[:4].isdigit():
            year = value[:4]
            break
    return str(row.get("title") or row.get("题名") or "").strip(), year


def matrix_by_title_year(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {
        (str(row.get("title", "")).strip(), str(row.get("year", "")).strip()): row
        for row in rows
        if row.get("title")
    }


def existing_fulltext_count(rows: list[dict], project: str) -> int:
    count = 0
    for row in rows:
        if project not in str(row.get("project_tags", "")):
            continue
        path = str(row.get("pdf_path", "")).strip()
        suffix = Path(path).suffix.lower()
        if suffix in FULLTEXT_SUFFIXES and (ROOT / path).exists():
            count += 1
        elif suffix in FULLTEXT_SUFFIXES and Path(path).exists():
            count += 1
    return count


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def has_existing_download(row: dict) -> bool:
    path_value = str(row.get("pdf_path", "")).strip()
    if Path(path_value).suffix.lower() not in FULLTEXT_SUFFIXES:
        return False
    return resolve_path(path_value).exists()


def validate_download(path: Path) -> dict:
    proc = subprocess.run(["file", str(path)], text=True, capture_output=True)
    file_text = (proc.stdout or proc.stderr).strip()
    is_pdf = "PDF document" in file_text
    suspicious = any(token in file_text for token in ("HTML document", "XML", "JSON text", "Unicode text"))
    page_count = ""
    if is_pdf:
        pdfinfo = subprocess.run(["pdfinfo", str(path)], text=True, capture_output=True)
        for line in (pdfinfo.stdout or "").splitlines():
            if line.startswith("Pages:"):
                page_count = line.split(":", 1)[1].strip()
                break
    suffix = path.suffix.lower()
    kind = "pdf" if is_pdf else suffix.lstrip(".") or "unknown"
    is_supported = (suffix in FULLTEXT_SUFFIXES or is_pdf) and not suspicious
    return {"is_supported": is_supported, "is_pdf": is_pdf, "kind": kind, "file": file_text, "pages": page_count}


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch download CNKI full texts from collected detail-page URLs.")
    parser.add_argument("--metadata-json", required=True, type=Path)
    parser.add_argument("--project", default="library_short_video")
    parser.add_argument("--target-total", type=int, default=60, help="Stop when this many project rows have local PDFs.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum download attempts in this run; 0 means no extra limit.")
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--nav-timeout", type=float, default=25)
    parser.add_argument("--target-dir", type=Path, default=ROOT / "library" / "pdfs" / "library_short_video")
    parser.add_argument("--update-matrix", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--probe-url",
        default=None,
        help="Navigate to a CNKI detail URL and print PDF/download candidates. Pass an empty string to probe the current tab.",
    )
    parser.add_argument("--delay-min", type=float, default=20.0, help="Minimum seconds to wait between attempts.")
    parser.add_argument("--delay-max", type=float, default=35.0, help="Maximum seconds to wait between attempts.")
    parser.add_argument("--confirm-save-dialog", action="store_true", help="If a macOS Chrome save dialog appears after clicking PDF, press Return to save to the current folder.")
    parser.add_argument("--save-dialog-delay", type=float, default=1.2, help="Seconds to wait before checking for a save dialog.")
    parser.add_argument("--no-stop-on-barrier", action="store_true", help="Continue after CAPTCHA/login/permission barriers instead of stopping this run.")
    parser.add_argument("--profile-filter", action="store_true", help="Skip rows that do not satisfy the project's recommendation_profile required/excluded terms.")
    parser.add_argument("--profile-path", type=Path, help="Recommendation profile JSON; defaults to projects/<project>/literature/recommendation_profile.json.")
    parser.add_argument("--allow-non-pdf-fallback", action="store_true", help="If detail-page PDF is unavailable, accept CNKI CAJ/NH/KDH download links as local full-text stock.")
    args = parser.parse_args()

    if args.probe_url is not None:
        nav = chrome_state()
        if args.probe_url:
            nav = navigate_to(args.probe_url, timeout=args.nav_timeout)
        print(json.dumps({"nav": nav, "probe": probe_pdf_candidates()}, ensure_ascii=False, indent=2))
        return 0

    export_rows = load_export_rows(args.metadata_json)
    profile_path = args.profile_path or ROOT / "projects" / args.project / "literature" / "recommendation_profile.json"
    profile = load_profile(profile_path) if args.profile_filter else {}
    matrix_rows, fieldnames = load_matrix()
    index = matrix_by_title_year(matrix_rows)
    current_total = existing_fulltext_count(matrix_rows, args.project)
    needed = max(0, args.target_total - current_total)
    max_attempts = needed if not args.limit else min(needed, args.limit)
    report: list[dict] = []

    if needed <= 0:
        print(json.dumps({"status": "already_satisfied", "existing_fulltext_count": current_total}, ensure_ascii=False, indent=2))
        return 0

    attempts = 0
    for export_row in export_rows:
        if attempts >= max_attempts:
            break
        title, year = title_year(export_row)
        matrix_row = index.get((title, year))
        if not matrix_row:
            report.append({"title": title, "year": year, "status": "missing_from_matrix"})
            continue
        if args.project not in str(matrix_row.get("project_tags", "")):
            continue
        if args.profile_filter and not matches_profile(export_row, matrix_row, profile):
            report.append({"title": title, "citekey": matrix_row.get("citekey"), "status": "profile_filtered"})
            continue
        if has_existing_download(matrix_row):
            continue
        detail_url = str(export_row.get("detail_url") or export_row.get("详情链接") or "").strip()
        if not detail_url:
            report.append({"title": title, "citekey": matrix_row.get("citekey"), "status": "missing_detail_url"})
            continue

        attempts += 1
        citekey = str(matrix_row.get("citekey"))
        started_at = time.time()
        stop_after_attempt = False
        try:
            nav = navigate_to(detail_url, timeout=args.nav_timeout)
            barrier = access_barrier_from_state(nav)
            if barrier:
                report.append({"title": title, "citekey": citekey, "status": "access_barrier", "barrier": barrier, "nav": nav})
                if not args.no_stop_on_barrier:
                    stop_after_attempt = True
                    break
                continue
            if not title_matches_page(title, str(nav.get("title", "")), str(nav.get("body", ""))):
                report.append(
                    {
                        "title": title,
                        "citekey": citekey,
                        "status": "page_title_mismatch",
                        "expected_title": title,
                        "page_title": nav.get("title", ""),
                        "page_url": nav.get("url", ""),
                    }
                )
                continue
            clicked = click_download(args.allow_non_pdf_fallback)
            if not clicked.get("ok"):
                report.append({"title": title, "citekey": citekey, "status": "click_failed", "nav": nav, "detail": clicked})
                if clicked.get("reason") == "access_barrier" and not args.no_stop_on_barrier:
                    stop_after_attempt = True
                    break
                continue
            if args.confirm_save_dialog:
                clicked["save_dialog"] = confirm_save_dialog_if_present(args.save_dialog_delay)
            suffixes = {".pdf"} if not args.allow_non_pdf_fallback else FULLTEXT_SUFFIXES
            source_name = wait_for_download(title, started_at, timeout=args.timeout, suffixes=suffixes)
            if not source_name and clicked.get("rect") and clicked.get("screen"):
                clicked["mouse_click"] = mouse_click_download_target(clicked)
                if args.confirm_save_dialog:
                    clicked["save_dialog_after_mouse"] = confirm_save_dialog_if_present(args.save_dialog_delay)
                source_name = wait_for_download(title, started_at, timeout=max(20.0, args.timeout / 2), suffixes=suffixes)
            if not source_name and clicked.get("href"):
                open_direct_url(str(clicked["href"]))
                if args.confirm_save_dialog:
                    clicked["save_dialog_after_href"] = confirm_save_dialog_if_present(args.save_dialog_delay)
                source_name = wait_for_download(title, started_at, timeout=max(20.0, args.timeout / 2), suffixes=suffixes)
            if not source_name:
                report.append({"title": title, "citekey": citekey, "status": "download_not_found", "detail": clicked})
                continue
            suffix = Path(source_name).suffix.lower() or ".pdf"
            target_path = finder_duplicate_to_project(source_name, args.target_dir, f"{citekey}{suffix}")
            validation = validate_download(target_path)
            if not validation["is_supported"]:
                report.append(
                    {
                        "title": title,
                        "citekey": citekey,
                        "status": "unsupported_download_after_copy",
                        "source": source_name,
                        "path": str(target_path),
                        "validation": validation,
                    }
                )
                continue
            if args.update_matrix:
                matrix_row["pdf_path"] = str(target_path)
            current_total += 1
            report.append(
                {
                    "title": title,
                    "citekey": citekey,
                    "status": "copied_fulltext",
                    "source": source_name,
                    "path": str(target_path),
                    "kind": validation.get("kind", ""),
                    "pages": validation.get("pages", ""),
                    "fulltext_count": current_total,
                }
            )
        except Exception as exc:
            report.append({"title": title, "citekey": citekey, "status": "error", "error": str(exc)})
        finally:
            if not stop_after_attempt and attempts < max_attempts:
                sleep_between_attempts(args.delay_min, args.delay_max)

    if args.update_matrix:
        write_matrix(matrix_rows, fieldnames)
    report_path = args.report or ROOT / "library" / "cnki_exports" / args.project / f"cnki_pdf_download_report_{time.strftime('%Y%m%d-%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    copied_count = sum(1 for item in report if item.get("status") == "copied_fulltext")
    starting_count = current_total - copied_count
    print(
        json.dumps(
            {
                "attempts": attempts,
                "starting_fulltext_count": starting_count,
                "ending_fulltext_count": current_total,
                "starting_pdf_count": starting_count,
                "ending_pdf_count": current_total,
                "report": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    failed = [item for item in report if item.get("status") not in {"copied_fulltext"}]
    return 1 if attempts and failed and not any(item.get("status") == "copied_fulltext" for item in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
