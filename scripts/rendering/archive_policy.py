from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

from rendering.paths import (
    ARCHIVE_POLICY_HTML,
    ARCHIVE_POLICY_JSON,
    BACKUP_INDEX,
    ROOT,
    WORKFLOW_AUDIT_JSON,
    WORKFLOW_HEALTH,
)


BACKUP_KEEP = 30
LOG_COMPACT_AFTER_DAYS = 45


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    item = Path(path)
    try:
        return str(item.relative_to(ROOT))
    except ValueError:
        return str(item)


def file_age_days(path: Path, now: dt.datetime) -> float:
    return max(0.0, (now.timestamp() - path.stat().st_mtime) / 86400)


def backup_state(now: dt.datetime) -> dict[str, Any]:
    backup_dir = ROOT / "backups"
    zips = sorted(backup_dir.glob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True) if backup_dir.exists() else []
    prune = zips[BACKUP_KEEP:]
    latest = zips[0] if zips else None
    return {
        "keep_newest": BACKUP_KEEP,
        "count": len(zips),
        "latest": rel(latest) if latest else "",
        "latest_age_days": round(file_age_days(latest, now), 2) if latest else None,
        "prune_candidates": [
            {
                "path": rel(path),
                "age_days": round(file_age_days(path, now), 2),
                "bytes": path.stat().st_size,
            }
            for path in prune
        ],
    }


def log_state(now: dt.datetime) -> dict[str, Any]:
    daily_dir = ROOT / "vault" / "07_Codex_Logs" / "daily"
    compact_dir = ROOT / "vault" / "07_Codex_Logs" / "compact_daily"
    daily_logs = sorted(daily_dir.glob("*.md")) if daily_dir.exists() else []
    compact_logs = sorted(compact_dir.glob("*.md")) if compact_dir.exists() else []
    compact_names = {path.name.replace("-summary", "") for path in compact_logs}
    candidates = []
    for path in daily_logs:
        age = file_age_days(path, now)
        if age >= LOG_COMPACT_AFTER_DAYS and path.name not in compact_names:
            candidates.append({"path": rel(path), "age_days": round(age, 2), "status": "needs_compact"})
    return {
        "daily_count": len(daily_logs),
        "compact_count": len(compact_logs),
        "compact_after_days": LOG_COMPACT_AFTER_DAYS,
        "compact_candidates": candidates,
    }


def cache_state() -> dict[str, Any]:
    ds_store = [path for path in ROOT.rglob(".DS_Store") if "backups" not in path.parts]
    pycache = [path for path in ROOT.rglob("__pycache__") if "backups" not in path.parts]
    return {
        "ds_store_count": len(ds_store),
        "pycache_count": len(pycache),
        "safe_cleanup_candidates": [rel(path) for path in [*ds_store[:20], *pycache[:20]]],
    }


def generated_state() -> dict[str, Any]:
    generated_dirs = [
        ROOT / "paper_reading" / "views",
        ROOT / "paper_reading" / "views" / "directories",
        ROOT / "knowledge_cards" / "views",
        ROOT / "logs" / "views",
        ROOT / "search",
    ]
    html_files: list[Path] = []
    for directory in generated_dirs:
        if directory.exists():
            html_files.extend(directory.glob("*.html"))
    return {
        "generated_html_count": len(html_files),
        "managed_by": "make learning-dashboard",
        "stale_cleanup": "生成器按 manifest/路由清理可重建 HTML；不要手工删除源 Markdown。",
    }


def build_archive_policy() -> dict[str, Any]:
    now = dt.datetime.now()
    backups = backup_state(now)
    logs = log_state(now)
    caches = cache_state()
    generated = generated_state()
    actions = [
        {
            "id": "backup-prune",
            "title": f"备份包保留最近 {BACKUP_KEEP} 个",
            "mode": "manual_destructive",
            "command": f"make workflow-backup-prune KEEP={BACKUP_KEEP}",
            "reason": "只删除超出保留窗口的 zip 备份包，不触碰源文件。",
            "candidate_count": len(backups.get("prune_candidates", [])),
        },
        {
            "id": "log-compact",
            "title": f"超过 {LOG_COMPACT_AFTER_DAYS} 天的 daily log 应有 compact summary",
            "mode": "automatic_report",
            "command": "make codex-compact-all BEFORE=<YYYY-MM-DD>",
            "reason": "压缩旧日志以降低上下文负担；原始日志默认保留。",
            "candidate_count": len(logs.get("compact_candidates", [])),
        },
        {
            "id": "cache-clean",
            "title": "系统缓存文件可安全清理",
            "mode": "manual_safe_cleanup",
            "command": "find . -name .DS_Store -delete && find . -name __pycache__ -type d -prune -exec rm -rf {} +",
            "reason": "只清理 macOS/Python 缓存；不影响研究源资产。",
            "candidate_count": caches.get("ds_store_count", 0) + caches.get("pycache_count", 0),
        },
    ]
    return {
        "schema_version": "1.0",
        "generated_at": now.isoformat(timespec="seconds"),
        "entrypoint": rel(ARCHIVE_POLICY_HTML),
        "summary": {
            "backup_count": backups.get("count", 0),
            "backup_prune_candidates": len(backups.get("prune_candidates", [])),
            "daily_log_count": logs.get("daily_count", 0),
            "compact_candidates": len(logs.get("compact_candidates", [])),
            "cache_candidates": caches.get("ds_store_count", 0) + caches.get("pycache_count", 0),
            "generated_html_count": generated.get("generated_html_count", 0),
        },
        "policy": {
            "canonical_sources": "Markdown、CSV、YAML、项目状态 JSON 和图谱状态 JSON 默认长期保留。",
            "generated_assets": "HTML 展示页、搜索页、总状态页和行动队列可由脚本重建，但仍随 Git 快照保留。",
            "backup_retention": f"zip 备份保留最近 {BACKUP_KEEP} 个；超出部分只通过显式 prune 命令删除。",
            "logs": f"daily log 默认保留；超过 {LOG_COMPACT_AFTER_DAYS} 天应有 compact summary。",
            "raw_files": "PDF、CAJ/KDH、原始数据和大型二进制不进 Git，归属外部材料库。",
            "safety": "自动化只报告和生成索引；删除或移动不确定文件必须显式命令执行。",
        },
        "entrypoints": {
            "backup_index": rel(BACKUP_INDEX),
            "workflow_health": rel(WORKFLOW_HEALTH),
            "audit_data": rel(WORKFLOW_AUDIT_JSON),
        },
        "backups": backups,
        "logs": logs,
        "generated": generated,
        "caches": caches,
        "actions": actions,
    }


def write_archive_policy_html(state: dict[str, Any]) -> None:
    summary = state.get("summary", {})
    policy = state.get("policy", {})
    actions = state.get("actions", [])
    action_rows = "\n".join(
        f"""
        <article class="action">
          <h2>{html.escape(str(action.get("title", "")))}</h2>
          <p>{html.escape(str(action.get("reason", "")))}</p>
          <p class="meta">{html.escape(str(action.get("mode", "")))} · candidates {action.get("candidate_count", 0)}</p>
          <code>{html.escape(str(action.get("command", "")))}</code>
        </article>
        """
        for action in actions
    )
    policy_rows = "\n".join(f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>" for key, value in policy.items())
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>自动归档策略</title>
  <style>
    :root {{ --ink:#1e293b; --muted:#64748b; --line:#dbe4ee; --paper:#fff; --soft:#f8fafc; --blue:#2563eb; --amber:#a15c07; --ring:rgba(37,99,235,.34); --shadow:0 10px 28px rgba(15,23,42,.06); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",Arial,sans-serif; color:var(--ink); background:#f8fafc; line-height:1.6; }}
    header {{ background:var(--paper); border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:1160px; margin:0 auto; padding:28px 22px; }}
    h1 {{ margin:0 0 8px; font-size:34px; }}
    h2 {{ margin:0 0 8px; font-size:18px; }}
    a {{ color:var(--blue); text-decoration:none; text-underline-offset:3px; }}
    a:hover {{ text-decoration:underline; }}
    a:focus-visible {{ outline:3px solid var(--ring); outline-offset:2px; border-radius:7px; }}
    .skip-link {{ position:absolute; left:18px; top:10px; z-index:20; transform:translateY(-140%); background:var(--ink); color:#fff; padding:8px 12px; border-radius:7px; }}
    .skip-link:focus {{ transform:translateY(0); }}
    code {{ display:inline-block; max-width:100%; overflow:auto; background:#eef3f8; border:1px solid #d8e2ec; border-radius:5px; padding:4px 6px; }}
    .sub,.meta {{ color:var(--muted); }}
    .nav {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
    .nav a {{ min-height:40px; padding:7px 11px; border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); transition:background-color 160ms ease,border-color 160ms ease,color 160ms ease; }}
    .nav a:hover {{ border-color:#bfcee0; background:#f8fbff; text-decoration:none; }}
    .nav a[aria-current="page"] {{ border-color:#b9ccff; background:#eef4ff; color:#1d4ed8; font-weight:650; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:14px; }}
    .metric,.panel,.action {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:var(--shadow); }}
    .metric b {{ display:block; font-size:28px; line-height:1.1; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .action {{ border-left:4px solid var(--amber); margin-bottom:10px; }}
    table {{ display:block; width:100%; max-width:100%; overflow-x:auto; border-collapse:collapse; -webkit-overflow-scrolling:touch; }}
    th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:8px 6px; vertical-align:top; }}
    th {{ color:var(--muted); width:210px; }}
    @media (max-width:820px) {{ .metrics,.grid {{ grid-template-columns:1fr; }} h1 {{ font-size:28px; }} .wrap {{ padding-left:16px; padding-right:16px; }} .nav {{ flex-wrap:nowrap; overflow-x:auto; padding-bottom:4px; }} .nav a {{ flex:0 0 auto; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ transition-duration:.01ms!important; animation-duration:.01ms!important; animation-iteration-count:1!important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <header>
    <div class="wrap">
      <h1>自动归档策略</h1>
      <p class="sub">Generated {html.escape(str(state.get("generated_at", "")))} · 自动化报告归档状态，但不删除不确定研究文件。</p>
      <nav class="nav">
        <a href="archive_policy.html" aria-current="page">归档策略</a>
        <a href="workflow_state.html">工作流总状态</a>
        <a href="workflow_health.html">工作流体检</a>
        <a href="backups/index.html">备份索引</a>
        <a href="project_collaboration.html">项目协作层</a>
      </nav>
    </div>
  </header>
  <main class="wrap" id="main-content">
    <section class="metrics">
      <div class="metric"><b>{summary.get("backup_count", 0)}</b><span class="meta">备份包</span></div>
      <div class="metric"><b>{summary.get("backup_prune_candidates", 0)}</b><span class="meta">可裁剪备份</span></div>
      <div class="metric"><b>{summary.get("compact_candidates", 0)}</b><span class="meta">待压缩日志</span></div>
      <div class="metric"><b>{summary.get("cache_candidates", 0)}</b><span class="meta">缓存候选</span></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>策略</h2>
        <table><tbody>{policy_rows}</tbody></table>
      </div>
      <div class="panel">
        <h2>建议动作</h2>
        {action_rows}
      </div>
    </section>
  </main>
</body>
</html>
"""
    ARCHIVE_POLICY_HTML.write_text(html_text, encoding="utf-8")


def write_archive_policy() -> tuple[Path, Path]:
    ARCHIVE_POLICY_JSON.parent.mkdir(parents=True, exist_ok=True)
    state = build_archive_policy()
    ARCHIVE_POLICY_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_archive_policy_html(state)
    return ARCHIVE_POLICY_JSON, ARCHIVE_POLICY_HTML
