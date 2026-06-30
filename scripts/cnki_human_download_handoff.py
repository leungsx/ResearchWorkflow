#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cnki_daily_recommend as daily


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
PROJECTS = ROOT / "projects"
REQUEST_ROOT = ROOT / "vault" / "15_CNKI_Frontier" / "download_requests"
FULLTEXT_SUFFIXES = {".pdf", ".caj", ".kdh", ".nh"}


@dataclass
class RequestItem:
    rank: int
    citekey: str
    title: str
    authors: str
    year: str
    source: str
    score: float
    cited_count: str
    download_count: str
    detail_url: str
    reasons: list[str]
    preferred_stem: str


def clean(value: str | None) -> str:
    return daily.clean(value)


def rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def safe_filename(value: str, limit: int = 64) -> str:
    text = re.sub(r"[\\/:*?\"<>|\s]+", "_", clean(value))
    text = re.sub(r"_+", "_", text).strip("._")
    return text[:limit].strip("._") or "paper"


def normalize_title(value: str) -> str:
    return re.sub(r"[\s_《》<>“”\"'，,。．.：:；;、（）()\[\]【】\-—]+", "", value or "").lower()


def parse_date(value: str | None) -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.date.today()


def file_signature(path: Path) -> str:
    with path.open("rb") as handle:
        return handle.read(12).hex()


def looks_like_pdf(path: Path) -> bool:
    try:
        return path.read_bytes()[:5] == b"%PDF-"
    except OSError:
        return False


def existing_fulltext(row: dict[str, str], project: str) -> Path | None:
    path = daily.resolve_path(row.get("pdf_path", ""))
    if path and path.exists() and path.suffix.lower() in FULLTEXT_SUFFIXES:
        return path
    citekey = clean(row.get("citekey"))
    if not citekey:
        return None
    base = ROOT / "library" / "pdfs" / project
    for suffix in sorted(FULLTEXT_SUFFIXES):
        candidate = base / f"{citekey}{suffix}"
        if candidate.exists():
            return candidate
    converted = base / "converted" / f"{citekey}.pdf"
    return converted if converted.exists() else None


def direct_project_fit(row: dict[str, str], profile: dict[str, Any]) -> bool:
    blob = clean("\n".join([row.get("title", ""), row.get("core_findings", ""), row.get("target_journal_relevance", "")]))
    groups = profile.get("required_term_groups", []) or []
    if groups:
        for group in groups:
            terms = [clean(item) for item in group if clean(item)]
            if terms and not any(term in blob for term in terms):
                return False
        return True
    return True


def select_candidates(
    project: str,
    topic: str,
    stage: str,
    day: dt.date,
    limit: int,
    profile_path: Path | None,
    allow_external: bool,
) -> tuple[list[daily.Candidate], dict[str, Any], Path, str]:
    profile, resolved_profile_path, _ = daily.ensure_profile(project, topic, profile_path)
    state, _ = daily.load_state(project)
    stage_value = daily.auto_stage(profile, state, day.isoformat()) if stage == "auto" else stage
    rows = daily.load_matrix(MATRIX, project)
    metadata, _ = daily.load_export_metadata(project)
    ranked = daily.rank_candidates(rows, metadata, profile, project, stage_value, day.isoformat(), state)
    selected: list[daily.Candidate] = []
    for candidate in ranked:
        if existing_fulltext(candidate.row, project):
            continue
        if not allow_external and not direct_project_fit(candidate.row, profile):
            continue
        selected.append(candidate)
        if len(selected) >= limit:
            break
    return selected, profile, resolved_profile_path, stage_value


def build_items(candidates: list[daily.Candidate]) -> list[RequestItem]:
    items: list[RequestItem] = []
    for index, candidate in enumerate(candidates, start=1):
        row = candidate.row
        meta = candidate.meta
        citekey = clean(row.get("citekey")) or f"candidate_{index:02d}"
        title = clean(row.get("title")) or clean(meta.get("title"))
        stem = f"{index:02d}_{citekey}_{safe_filename(title, 44)}"
        items.append(
            RequestItem(
                rank=index,
                citekey=citekey,
                title=title,
                authors=clean(row.get("authors")) or clean(meta.get("authors")),
                year=clean(row.get("year")) or clean(meta.get("year")),
                source=clean(row.get("source")) or clean(meta.get("source")),
                score=round(candidate.score, 2),
                cited_count=clean(meta.get("cited_count")),
                download_count=clean(meta.get("download_count")),
                detail_url=clean(meta.get("detail_url")),
                reasons=candidate.reasons[:6],
                preferred_stem=stem,
            )
        )
    return items


def project_search_queries(project: str, profile: dict[str, Any]) -> list[str]:
    if project == "library_short_video":
        return [
            "主题 = 图书馆 AND 主题 = 短视频",
            "主题 = 公共图书馆 AND 主题 = 短视频",
            "主题 = 高校图书馆 AND 主题 = 短视频",
            "主题 = 阅读推广 AND 主题 = 短视频",
            "主题 = 图书馆 AND (主题 = 抖音 OR 主题 = 快手 OR 主题 = 视频号 OR 主题 = B站 OR 主题 = 哔哩哔哩)",
        ]
    terms = [clean(item) for item in profile.get("include_terms", []) if clean(item)]
    if len(terms) >= 2:
        return [f"主题 = {terms[0]} AND 主题 = {terms[1]}"]
    topic = clean(profile.get("topic")) or "当前研究主题"
    return [f"主题 = {topic}"]


def request_paths(project: str, day: dt.date) -> tuple[Path, Path, Path, Path]:
    request_dir = REQUEST_ROOT / project
    request_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{day.isoformat()}-{project}-cnki-download-request"
    md_path = request_dir / f"{stem}.md"
    html_path = request_dir / f"{stem}.html"
    csv_path = request_dir / f"{stem}.csv"
    incoming_dir = ROOT / "library" / "pdfs" / project / "incoming" / day.isoformat()
    incoming_dir.mkdir(parents=True, exist_ok=True)
    return md_path, html_path, csv_path, incoming_dir


def write_csv(path: Path, items: list[RequestItem], incoming_dir: Path) -> None:
    fields = [
        "rank",
        "citekey",
        "title",
        "authors",
        "year",
        "source",
        "score",
        "cited_count",
        "download_count",
        "detail_url",
        "preferred_filename_stem",
        "incoming_dir",
        "status",
        "local_file",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "rank": item.rank,
                    "citekey": item.citekey,
                    "title": item.title,
                    "authors": item.authors,
                    "year": item.year,
                    "source": item.source,
                    "score": item.score,
                    "cited_count": item.cited_count,
                    "download_count": item.download_count,
                    "detail_url": item.detail_url,
                    "preferred_filename_stem": item.preferred_stem,
                    "incoming_dir": rel(incoming_dir),
                    "status": "pending",
                    "local_file": "",
                    "notes": "download PDF first; CAJ/KDH/NH accepted if PDF is unavailable",
                }
            )


def markdown_report(
    project: str,
    day: dt.date,
    topic: str,
    stage: str,
    profile_path: Path,
    md_path: Path,
    html_path: Path,
    csv_path: Path,
    incoming_dir: Path,
    items: list[RequestItem],
    queries: list[str],
) -> str:
    lines = [
        f"# CNKI 人工下载交接清单 - {project}",
        "",
        f"Date: {day.isoformat()}",
        f"Topic: {topic or project}",
        f"Stage: `{stage}`",
        f"Profile: `{rel(profile_path)}`",
        f"HTML view: `{rel(html_path)}`",
        f"Checklist CSV: `{rel(csv_path)}`",
        f"Download folder: `{rel(incoming_dir)}`",
        "",
        "## 操作边界",
        "",
        "- 用户使用自己的合法 CNKI / 机构 / 图书馆访问权限下载全文。",
        "- Codex 不接收账号密码，不绕过验证码、付费墙、下载限制或机构权限。",
        "- 优先下载 PDF；没有 PDF 时，可下载 CAJ/KDH/NH，后续由本地转换流程处理。",
        "",
        "## CNKI 检索步骤",
        "",
        "1. 打开 CNKI 高级检索：https://kns.cnki.net/kns8/AdvSearch",
        "2. 使用下列检索式之一，优先选择 `主题` 字段；若噪声过高，再切换 `篇名` 字段。",
    ]
    for query in queries:
        lines.append(f"   - `{query}`")
    lines.extend(
        [
            "3. 时间范围优先 `2019-2026`；文献类型优先期刊。",
            "4. 先按被引/下载/相关度识别高价值论文，再按最新排序补近期文献。",
            "5. 对照下方下载清单逐篇打开详情页，优先点详情页 `PDF下载`。",
            f"6. 下载后放入：`{incoming_dir}`。",
            "7. 文件名建议包含 citekey，例如：`01_cnki_xxx_论文短标题.pdf`；这样我能自动匹配。",
            "",
            "## 下载清单",
            "",
            "| Rank | Citekey | Title | Year | Source | CNKI signal | Suggested filename stem | Why download |",
            "|---:|---|---|---:|---|---|---|---|",
        ]
    )
    for item in items:
        signal = f"被引 {item.cited_count or 'NA'} / 下载 {item.download_count or 'NA'}"
        why = "；".join(item.reasons[:3])
        lines.append(
            f"| {item.rank} | `{item.citekey}` | {item.title.replace('|', '/')} | {item.year} | {item.source.replace('|', '/')} | {signal} | `{item.preferred_stem}` | {why.replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## 下载后交接",
            "",
            "下载完成后运行：",
            "",
            "```bash",
            f"make cnki-intake PROJECT={project} REQUEST={rel(csv_path)}",
            "```",
            "",
            "如果要立刻生成 PDF Reader：",
            "",
            "```bash",
            f"make cnki-intake PROJECT={project} REQUEST={rel(csv_path)} BUILD_READERS=1",
            "```",
            "",
            "CAJ/KDH/NH 文件入库后再运行：",
            "",
            "```bash",
            f"make caj-convert PROJECT={project} SCAN=1",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def html_report(
    project: str,
    day: dt.date,
    topic: str,
    stage: str,
    csv_path: Path,
    incoming_dir: Path,
    items: list[RequestItem],
    queries: list[str],
) -> str:
    query_chips = "\n".join(f"<code>{html.escape(query)}</code>" for query in queries)
    rows = "\n".join(
        f"""
        <tr>
          <td class="rank">{item.rank}</td>
          <td><strong>{html.escape(item.title)}</strong><br><span>{html.escape(item.authors)} · {html.escape(item.year)} · {html.escape(item.source)}</span></td>
          <td><code>{html.escape(item.citekey)}</code></td>
          <td>{html.escape(item.cited_count or 'NA')} / {html.escape(item.download_count or 'NA')}</td>
          <td><code>{html.escape(item.preferred_stem)}</code></td>
          <td>{html.escape('；'.join(item.reasons[:3]))}</td>
          <td>{f'<a href="{html.escape(item.detail_url)}">详情</a>' if item.detail_url else '<span class="muted">按题名检索</span>'}</td>
        </tr>
        """
        for item in items
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CNKI 人工下载交接清单 - {html.escape(project)}</title>
  <style>
    :root {{ --ink:#17212b; --muted:#647386; --line:#d8e1ea; --paper:#fff; --bg:#f4f7fb; --blue:#2457d6; --green:#146c5a; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:radial-gradient(circle at 88% 0%, rgba(36,87,214,.13), transparent 34%), var(--bg); line-height:1.55; }}
    header {{ background:#112235; color:white; }}
    .wrap {{ max-width:1220px; margin:0 auto; padding:26px 22px; }}
    h1 {{ margin:0 0 8px; font-size:32px; }}
    h2 {{ margin:0 0 12px; font-size:21px; }}
    a {{ color:var(--blue); text-decoration:none; }}
    .sub {{ color:rgba(255,255,255,.78); }}
    .grid {{ display:grid; grid-template-columns:1.1fr .9fr; gap:16px; margin:20px 0; }}
    .card {{ background:var(--paper); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 14px 34px rgba(17,34,53,.07); }}
    code {{ background:#eef3f9; border:1px solid #dbe5ef; border-radius:7px; padding:2px 6px; }}
    .queries {{ display:flex; flex-direction:column; gap:8px; }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; background:white; border:1px solid var(--line); border-radius:18px; overflow:hidden; box-shadow:0 14px 34px rgba(17,34,53,.06); }}
    th, td {{ text-align:left; vertical-align:top; padding:12px 13px; border-bottom:1px solid var(--line); }}
    th {{ color:#526273; font-size:13px; background:#f8fafc; }}
    tr:last-child td {{ border-bottom:0; }}
    td span, .muted {{ color:var(--muted); }}
    .rank {{ font-size:22px; font-weight:800; color:var(--green); }}
    .actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
    .btn {{ display:inline-block; background:var(--blue); color:white; padding:9px 13px; border-radius:999px; }}
    .btn.secondary {{ background:#e7eef7; color:#1b334d; }}
    @media (max-width: 920px) {{ .grid {{ grid-template-columns:1fr; }} table {{ font-size:13px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>CNKI 人工下载交接清单</h1>
      <p class="sub">{html.escape(project)} · {day.isoformat()} · {html.escape(topic or project)} · stage: {html.escape(stage)}</p>
      <div class="actions">
        <a class="btn" href="https://kns.cnki.net/kns8/AdvSearch">打开 CNKI 高级检索</a>
        <a class="btn secondary" href="{html.escape(csv_path.name)}">下载 CSV 清单</a>
      </div>
    </div>
  </header>
  <main class="wrap">
    <section class="grid">
      <article class="card">
        <h2>怎么做</h2>
        <p>你使用自己的合法 CNKI / 机构访问权限下载全文。我负责筛选清单、目标文件夹、入库验收、Reader 和后续推荐分析。</p>
        <p>目标文件夹：<code>{html.escape(str(incoming_dir))}</code></p>
        <p>优先点详情页 <strong>PDF下载</strong>；没有 PDF 时，CAJ/KDH/NH 也可以先下载，后续本地转换。</p>
      </article>
      <article class="card">
        <h2>推荐检索式</h2>
        <div class="queries">{query_chips}</div>
      </article>
    </section>
    <table>
      <thead><tr><th>#</th><th>论文</th><th>Citekey</th><th>被引/下载</th><th>建议文件名 stem</th><th>推荐理由</th><th>CNKI</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </main>
</body>
</html>
"""


def open_cnki() -> None:
    subprocess.run(["open", "https://kns.cnki.net/kns8/AdvSearch"], check=False)


def command_request(args: argparse.Namespace) -> int:
    day = parse_date(args.date)
    selected, profile, profile_path, stage = select_candidates(
        args.project,
        args.topic,
        args.stage,
        day,
        args.count,
        args.profile,
        args.allow_external,
    )
    items = build_items(selected)
    md_path, html_path, csv_path, incoming_dir = request_paths(args.project, day)
    queries = project_search_queries(args.project, profile)

    write_csv(csv_path, items, incoming_dir)
    md = markdown_report(
        args.project,
        day,
        args.topic or clean(profile.get("topic")),
        stage,
        profile_path,
        md_path,
        html_path,
        csv_path,
        incoming_dir,
        items,
        queries,
    )
    md_path.write_text(md + "\n", encoding="utf-8")
    html_path.write_text(
        html_report(args.project, day, args.topic or clean(profile.get("topic")), stage, csv_path, incoming_dir, items, queries),
        encoding="utf-8",
    )
    if args.open_cnki:
        open_cnki()
    print(f"Wrote CNKI handoff markdown: {md_path}")
    print(f"Wrote CNKI handoff HTML: {html_path}")
    print(f"Wrote CNKI handoff CSV: {csv_path}")
    print(f"Download folder: {incoming_dir}")
    print(f"Candidates: {len(items)}")
    return 0


def read_request_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_request(project: str) -> Path | None:
    request_dir = REQUEST_ROOT / project
    files = sorted(request_dir.glob("*-cnki-download-request.csv"), key=lambda item: item.stat().st_mtime, reverse=True)
    return files[0] if files else None


def candidate_files(incoming_dir: Path) -> list[Path]:
    if not incoming_dir.exists():
        return []
    return sorted(path for path in incoming_dir.iterdir() if path.is_file() and path.suffix.lower() in FULLTEXT_SUFFIXES)


def match_file(row: dict[str, str], files: list[Path], used: set[Path]) -> Path | None:
    citekey = clean(row.get("citekey"))
    stem = clean(row.get("preferred_filename_stem"))
    title_key = normalize_title(row.get("title", ""))
    for path in files:
        if path in used:
            continue
        name = path.stem
        if citekey and citekey in name:
            return path
        if stem and stem in name:
            return path
    for path in files:
        if path in used:
            continue
        if title_key and title_key[:16] and title_key[:16] in normalize_title(path.stem):
            return path
    return None


def load_matrix() -> tuple[list[dict[str, str]], list[str]]:
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_matrix(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with MATRIX.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_matrix_pdf_path(citekey: str, path: Path) -> bool:
    rows, fieldnames = load_matrix()
    changed = False
    for row in rows:
        if row.get("citekey") == citekey:
            row["pdf_path"] = rel(path)
            if not clean(row.get("read_status")):
                row["read_status"] = "metadata-only"
            changed = True
            break
    if changed:
        write_matrix(rows, fieldnames)
    return changed


def build_reader(project: str, citekey: str, path: Path) -> int:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "paper_reader.py"),
        "--project",
        project,
        "--citekey",
        citekey,
        "--pdf",
        str(path),
        "--update-matrix",
    ]
    return subprocess.run(cmd, cwd=ROOT).returncode


def command_intake(args: argparse.Namespace) -> int:
    request_csv = args.request or latest_request(args.project)
    if not request_csv:
        raise SystemExit(f"No request CSV found for project {args.project}. Run cnki-handoff first.")
    rows = read_request_csv(request_csv)
    incoming_dirs = [clean(row.get("incoming_dir")) for row in rows if clean(row.get("incoming_dir"))]
    incoming_dir = args.incoming_dir or (ROOT / incoming_dirs[0] if incoming_dirs else ROOT / "library" / "pdfs" / args.project / "incoming")
    target_dir = args.target_dir or (ROOT / "library" / "pdfs" / args.project)
    target_dir.mkdir(parents=True, exist_ok=True)

    files = candidate_files(incoming_dir)
    used: set[Path] = set()
    report_rows: list[dict[str, str]] = []
    copied = 0
    reader_built = 0
    needs_conversion = 0
    invalid = 0

    for row in rows:
        citekey = clean(row.get("citekey"))
        if not citekey:
            continue
        found = match_file(row, files, used)
        if not found:
            report_rows.append({**row, "intake_status": "missing", "stored_path": "", "message": "No matching file in incoming folder."})
            continue
        used.add(found)
        suffix = found.suffix.lower()
        if suffix == ".pdf" and not looks_like_pdf(found):
            invalid += 1
            report_rows.append(
                {
                    **row,
                    "intake_status": "invalid_pdf",
                    "stored_path": "",
                    "message": f"File extension is PDF but signature is {file_signature(found)}; likely HTML or failed download.",
                }
            )
            continue
        stored = target_dir / f"{citekey}{suffix}"
        if found.resolve() != stored.resolve():
            if args.move:
                shutil.move(str(found), stored)
            else:
                shutil.copy2(found, stored)
        update_matrix_pdf_path(citekey, stored)
        copied += 1
        message = "stored and matrix pdf_path updated"
        if suffix in {".caj", ".kdh", ".nh"}:
            needs_conversion += 1
            message += "; run caj-convert before building source-grounded reader"
        elif args.build_readers:
            code = build_reader(args.project, citekey, stored)
            if code == 0:
                reader_built += 1
                message += "; reader built"
            else:
                message += f"; reader command exited {code}"
        report_rows.append({**row, "intake_status": "stored", "stored_path": rel(stored), "message": message})

    report_path = request_csv.with_name(request_csv.stem.replace("-request", "-intake-report") + ".csv")
    fieldnames = list(report_rows[0].keys()) if report_rows else ["status"]
    with report_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    summary_path = report_path.with_suffix(".md")
    summary_path.write_text(
        "\n".join(
            [
                f"# CNKI Intake Report - {args.project}",
                "",
                f"Request: `{rel(request_csv)}`",
                f"Incoming folder: `{rel(incoming_dir)}`",
                f"Target folder: `{rel(target_dir)}`",
                "",
                f"- Stored: {copied}",
                f"- Readers built: {reader_built}",
                f"- Needs CAJ/KDH/NH conversion: {needs_conversion}",
                f"- Invalid PDF downloads: {invalid}",
                "",
                "Next commands:",
                "",
                "```bash",
                f"make caj-convert PROJECT={args.project} SCAN=1",
                f"make cnki-daily PROJECT={args.project}",
                "make learning-dashboard",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Request CSV: {request_csv}")
    print(f"Incoming folder: {incoming_dir}")
    print(f"Intake report CSV: {report_path}")
    print(f"Intake report markdown: {summary_path}")
    print(f"Stored={copied} ReadersBuilt={reader_built} NeedsConversion={needs_conversion} Invalid={invalid}")
    return 1 if invalid else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and process a human-in-the-loop CNKI full-text download handoff.")
    sub = parser.add_subparsers(dest="command", required=True)

    req = sub.add_parser("request", help="Create a CNKI manual download checklist.")
    req.add_argument("--project", default="library_short_video")
    req.add_argument("--topic", default="")
    req.add_argument("--stage", choices=["auto", *daily.STAGE_ORDER], default="auto")
    req.add_argument("--date")
    req.add_argument("--count", type=int, default=12)
    req.add_argument("--profile", type=Path)
    req.add_argument("--open-cnki", action="store_true")
    req.add_argument("--allow-external", action="store_true", help="Allow adjacent non-core papers as external comparison candidates.")
    req.set_defaults(func=command_request)

    intake = sub.add_parser("intake", help="Validate and ingest files downloaded by the user.")
    intake.add_argument("--project", default="library_short_video")
    intake.add_argument("--request", type=Path, help="Checklist CSV from the request step. Defaults to latest project request.")
    intake.add_argument("--incoming-dir", type=Path)
    intake.add_argument("--target-dir", type=Path)
    intake.add_argument("--build-readers", action="store_true")
    intake.add_argument("--move", action="store_true", help="Move files out of incoming instead of copying them.")
    intake.set_defaults(func=command_intake)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
