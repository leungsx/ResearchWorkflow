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
    ready_state: document.readyState,
    extracted_at: new Date().toISOString(),
    rows
  });
})()
"""


def run_chrome_js(script: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        js_path = fh.name
    try:
        osa = [
            "osascript",
            "-e",
            f'set jsCode to read POSIX file "{js_path}"',
            "-e",
            'tell application "Google Chrome" to execute active tab of front window javascript jsCode',
        ]
        proc = subprocess.run(osa, text=True, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        return proc.stdout.strip()
    finally:
        Path(js_path).unlink(missing_ok=True)


def submit_search(query: str, start_date: str, end_date: str) -> dict:
    script = f"""
(function() {{
  function setValue(el, value) {{
    if (!el) return false;
    el.focus();
    el.value = value;
    el.setAttribute("value", value);
    el.setAttribute("txt", value);
    el.setAttribute("condition", "(" + value + ")");
    el.dispatchEvent(new Event("input", {{bubbles: true}}));
    el.dispatchEvent(new Event("change", {{bubbles: true}}));
    el.dispatchEvent(new KeyboardEvent("keyup", {{bubbles: true, key: "Enter"}}));
    return true;
  }}
  var exactQuery = document.querySelector("#gradetxt dd:first-of-type .input-box input[type='text']") ||
    document.querySelector("#gradetxt .input-box input[type='text']");
  var nodes = document.querySelectorAll("input,textarea");
  var visible = [];
  for (var i = 0; i < nodes.length; i += 1) {{
    var e = nodes[i];
    if (e.offsetWidth || e.offsetHeight || e.getClientRects().length) visible.push(e);
  }}
  var queryInput = exactQuery || visible[0] || null;
  for (var j = 0; j < visible.length; j += 1) {{
    if (exactQuery) break;
    var label = String((visible[j].id || "") + " " + (visible[j].className || ""));
    if (!/date|year|time/i.test(label)) {{
      queryInput = visible[j];
      break;
    }}
  }}
  var queryOk = setValue(queryInput, {json.dumps(query, ensure_ascii=True)});
  var startOk = setValue(document.querySelector("#datebox0"), {json.dumps(start_date)});
  var endOk = setValue(document.querySelector("#datebox1"), {json.dumps(end_date)});
  var button = document.querySelector(".btn-search");
  if (!button) {{
    var buttons = document.querySelectorAll("button,a,input");
    for (var k = 0; k < buttons.length; k += 1) {{
      var text = String((buttons[k].innerText || "") + (buttons[k].value || "") + (buttons[k].title || ""));
      if (/检索|搜索|search/i.test(text)) {{
        button = buttons[k];
        break;
      }}
    }}
  }}
  if (!button) {{
    return JSON.stringify({{ok:false, reason:"search_button_not_found", title:document.title, url:location.href}});
  }}
  button.scrollIntoView({{block: "center", inline: "center"}});
  button.click();
  return JSON.stringify({{
    ok:true,
    queryOk,
    startOk,
    endOk,
    queryValue: queryInput ? queryInput.value : "",
    queryTxt: queryInput ? queryInput.getAttribute("txt") : "",
    title:document.title,
    url:location.href
  }});
}})()
"""
    return json.loads(run_chrome_js(script))


def wait_for_rows(timeout: float) -> dict:
    deadline = time.time() + timeout
    last: dict = {"ok": False, "reason": "not_checked"}
    while time.time() < deadline:
        data = json.loads(run_chrome_js(JS_EXTRACT_RESULTS))
        rows = data.get("rows", [])
        last = data
        if rows:
            data["ok"] = True
            return data
        time.sleep(1.0)
    last["ok"] = False
    last["reason"] = "no_rows_before_timeout"
    return last


def click_next_page() -> dict:
    script = r"""
(function() {
  function clean(value) { return String(value || "").replace(/\s+/g, " ").trim(); }
  function disabled(el) {
    var text = clean([el.className, el.getAttribute("aria-disabled"), el.disabled].join(" "));
    return /disabled|true/i.test(text);
  }
  var elements = document.querySelectorAll("a,button");
  var candidates = [];
  for (var i = 0; i < elements.length; i += 1) {
    var el = elements[i];
    var text = clean([el.innerText, el.title, el.getAttribute("aria-label"), el.className, el.id].join(" "));
    var score = 0;
    if (/下一页|下页|Next|next/i.test(text)) score += 80;
    if (/page-next|next/i.test(text)) score += 30;
    if (/›|>|»/.test(text)) score += 15;
    if (disabled(el)) score -= 100;
    if (score > 0) candidates.push({el: el, idx: i, text: text, href: el.href || "", score: score});
  }
  candidates.sort(function(a, b) { return b.score - a.score || a.idx - b.idx; });
  var chosen = candidates[0];
  if (!chosen) {
    var samples = [];
    for (var s = Math.max(0, elements.length - 80); s < elements.length; s += 1) {
      var sampleText = clean(elements[s].innerText || elements[s].title || elements[s].className || elements[s].id);
      if (sampleText) samples.push(sampleText);
    }
    return JSON.stringify({
      ok:false,
      reason:"next_button_not_found",
      title:document.title,
      url:location.href,
      samples:samples
    });
  }
  chosen.el.scrollIntoView({block:"center", inline:"center"});
  chosen.el.click();
  return JSON.stringify({ok:true, text:chosen.text, href:chosen.href, title:document.title, url:location.href});
})()
"""
    return json.loads(run_chrome_js(script))


def probe_form() -> dict:
    script = r"""
(() => {
  const clean = (value) => String(value || "").replace(/\s+/g, " ").trim();
  const fields = [...document.querySelectorAll("input,textarea,select")].map((el, idx) => ({
    idx,
    tag: el.tagName,
    type: el.type || "",
    id: el.id || "",
    name: el.name || "",
    className: String(el.className || ""),
    placeholder: el.getAttribute("placeholder") || "",
    value: el.value || "",
    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
  })).slice(0, 80);
  const buttons = [...document.querySelectorAll("button,a,input")].map((el, idx) => ({
    idx,
    tag: el.tagName,
    type: el.type || "",
    id: el.id || "",
    className: String(el.className || ""),
    text: clean(el.innerText || el.value || el.title || el.getAttribute("aria-label") || ""),
    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
  })).filter(x => x.text || x.id || x.className).slice(0, 120);
  return JSON.stringify({title: document.title, url: location.href, fields, buttons});
})()
"""
    return json.loads(run_chrome_js(script))


def probe_visible() -> dict:
    script = r"""
(() => {
  const clean = (value) => String(value || "").replace(/\s+/g, " ").trim();
  const fields = [...document.querySelectorAll("input,textarea,select")]
    .map((el, idx) => ({
      idx,
      tag: el.tagName,
      type: el.type || "",
      id: el.id || "",
      className: String(el.className || ""),
      placeholder: el.getAttribute("placeholder") || "",
      value: el.value || "",
      txt: el.getAttribute("txt") || "",
      condition: el.getAttribute("condition") || "",
      visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
    }))
    .filter(x => x.visible)
    .slice(0, 40);
  const buttons = [...document.querySelectorAll("button,a,input")]
    .map((el, idx) => ({
      idx,
      tag: el.tagName,
      type: el.type || "",
      id: el.id || "",
      className: String(el.className || ""),
      text: clean(el.innerText || el.value || el.title || el.getAttribute("aria-label") || ""),
      visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
    }))
    .filter(x => x.visible && (x.text || x.id || x.className))
    .slice(0, 80);
  return JSON.stringify({title: document.title, url: location.href, fields, buttons});
})()
"""
    return json.loads(run_chrome_js(script))


def write_outputs(rows: list[dict], meta: dict, csv_path: Path, json_path: Path, tag: str) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
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
                    "项目标签": tag,
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect multiple pages from the current CNKI result list.")
    parser.add_argument("--query", default="", help="If provided, submit the CNKI advanced search first.")
    parser.add_argument("--start-date", default="2019-01-01")
    parser.add_argument("--end-date", default="2026-06-21")
    parser.add_argument("--pages", type=int, default=3)
    parser.add_argument("--target-rows", type=int, default=60)
    parser.add_argument("--wait", type=float, default=25)
    parser.add_argument("--tag", default="")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--json", required=True)
    parser.add_argument("--probe-form", action="store_true", help="Print current form fields/buttons and exit.")
    parser.add_argument("--probe-visible", action="store_true", help="Print visible fields/buttons and exit.")
    args = parser.parse_args()

    if args.probe_form:
        print(json.dumps(probe_form(), ensure_ascii=False, indent=2))
        return 0
    if args.probe_visible:
        print(json.dumps(probe_visible(), ensure_ascii=False, indent=2))
        return 0

    events: list[dict] = []
    if args.query:
        submit_result = submit_search(args.query, args.start_date, args.end_date)
        events.append({"event": "submit_search", "result": submit_result})
        first = wait_for_rows(args.wait)
        events.append({"event": "wait_first_rows", "result": {k: first.get(k) for k in ("ok", "reason", "title", "url")}})
        if not first.get("ok"):
            raise SystemExit(json.dumps({"events": events, "form": probe_form()}, ensure_ascii=False, indent=2))

    collected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for page in range(1, args.pages + 1):
        data = wait_for_rows(args.wait)
        rows = data.get("rows", [])
        events.append({"event": "extract_page", "page": page, "rows": len(rows), "url": data.get("url")})
        for row in rows:
            key = (row.get("title", ""), row.get("published_at", ""))
            if key in seen:
                continue
            seen.add(key)
            item = dict(row)
            item["collected_page"] = page
            item["global_rank"] = len(collected) + 1
            collected.append(item)
            if len(collected) >= args.target_rows:
                break
        if len(collected) >= args.target_rows or page >= args.pages:
            break
        next_result = click_next_page()
        events.append({"event": "click_next", "page": page, "result": next_result})
        if not next_result.get("ok"):
            break
        time.sleep(2.5)

    csv_path = ROOT / args.csv if not Path(args.csv).is_absolute() else Path(args.csv)
    json_path = ROOT / args.json if not Path(args.json).is_absolute() else Path(args.json)
    write_outputs(
        collected,
        {
            "query": args.query,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "target_rows": args.target_rows,
            "events": events,
        },
        csv_path,
        json_path,
        args.tag,
    )
    print(f"Wrote CSV: {csv_path}")
    print(f"Wrote JSON: {json_path}")
    print(f"Rows: {len(collected)}")
    return 0 if collected else 1


if __name__ == "__main__":
    raise SystemExit(main())
