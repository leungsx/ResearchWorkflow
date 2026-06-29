#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
CNKI_EXPORTS = ROOT / "library" / "cnki_exports"
PROJECTS = ROOT / "projects"
OUT_DIR = ROOT / "vault" / "15_CNKI_Frontier" / "daily_recommendations"

# Daily discovery should surface the next unread paper. Upgrading a skimmed
# paper to human-read/verified is a separate, user-directed reading task.
BLOCKED_READ_STATUSES = {"skimmed", "human-read", "verified", "discarded"}

STAGE_ORDER = [
    "foundation_high_impact",
    "review_and_map",
    "recent_important",
    "method_model",
]

STAGE_LABELS = {
    "foundation_high_impact": "基础高影响",
    "review_and_map": "综述/现状地图",
    "recent_important": "近期重要研究",
    "method_model": "方法/模型深读",
}

STAGE_DESCRIPTIONS = {
    "foundation_high_impact": "先读领域内被引、下载、来源和贴合度都较强的论文，建立共同语言。",
    "review_and_map": "再读现状、问题、对策、比较和综述型论文，搭建主题地图。",
    "recent_important": "随后跟进近年重要研究，判断问题是否已经转向新平台、新机制或新证据。",
    "method_model": "最后拆解模型、变量、数据和方法，为后续选题或实证设计做储备。",
}

DEFAULT_PROFILE = {
    "topic": "",
    "include_terms": [],
    "required_term_groups": [],
    "exclude_terms": [],
    "target_sources": ["图书情报工作"],
    "strong_sources": [
        "大学图书馆学报",
        "图书情报知识",
        "图书馆论坛",
        "国家图书馆学刊",
        "情报资料工作",
        "图书馆建设",
    ],
    "field_sources": [
        "图书馆学研究",
        "图书馆",
        "图书馆工作与研究",
        "图书馆理论与实践",
        "图书与情报",
    ],
    "learning_sequence": STAGE_ORDER,
    "foundation_days": 5,
    "review_days": 3,
    "recent_days": 4,
    "notes": "Daily recommendations start from high-impact field papers, then review/map papers, then recent important studies, then method/model papers.",
}

META_ALIASES = {
    "title": ["title", "题名", "篇名", "标题"],
    "authors": ["authors", "author", "作者", "著者"],
    "source": ["source", "来源", "刊名", "期刊", "出版物"],
    "published_at": ["published_at", "发表时间", "发表日期", "出版时间", "日期", "year", "年份"],
    "publication_type": ["publication_type", "文献类型", "类型"],
    "cited_count": ["cited_count", "被引", "被引频次", "引用", "citation_count"],
    "download_count": ["download_count", "下载", "下载频次", "download"],
    "detail_url": ["detail_url", "详情链接", "URL", "url"],
    "download_url": ["download_url", "下载链接"],
    "html_url": ["html_url", "HTML链接"],
    "ai_read_url": ["ai_read_url", "AI阅读链接"],
    "rank": ["rank", "序号", "排名"],
}

REVIEW_TERMS = [
    "综述",
    "研究进展",
    "现状",
    "问题",
    "对策",
    "策略",
    "发展",
    "路径",
    "比较",
    "调查",
    "建设现状",
    "运营探析",
]

METHOD_TERMS = [
    "模型",
    "实证",
    "影响因素",
    "内容分析",
    "文献计量",
    "网络分析",
    "问卷",
    "访谈",
    "SICAS",
    "4P",
    "4C",
    "上瘾模型",
]


@dataclass
class Candidate:
    row: dict[str, str]
    meta: dict[str, str]
    stage: str
    score: float
    components: dict[str, float]
    reasons: list[str]
    reader_path: Path | None
    pdf_path: Path | None

    @property
    def citekey(self) -> str:
        return self.row.get("citekey", "")

    @property
    def title(self) -> str:
        return self.row.get("title", "")


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16", "utf-16le", "utf-16be"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def normalize_key(value: str) -> str:
    return re.sub(r"[\s_\-:：()（）\[\]【】]+", "", value.strip().lower())


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def table_cell(value: str | int | float | None) -> str:
    text = clean(str(value or ""))
    return text.replace("|", "\\|")


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(value: str) -> Path | None:
    value = clean(value)
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def parse_int(value: Any) -> int:
    text = clean(str(value or ""))
    if not text:
        return 0
    text = text.replace(",", "")
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else 0


def extract_year(*values: str) -> int:
    for value in values:
        match = re.search(r"(19|20)\d{2}", value or "")
        if match:
            return int(match.group(0))
    return 0


def first_value(row: dict[str, Any], field: str) -> str:
    aliases = {normalize_key(item) for item in META_ALIASES[field]}
    for key, value in row.items():
        if normalize_key(str(key)) in aliases:
            return clean(str(value or ""))
    return ""


def load_matrix(path: Path, project: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        row
        for row in rows
        if row.get("source_database", "").upper() == "CNKI"
        and project in row.get("project_tags", "")
    ]


def parse_csv_like(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel
    return [{key or "": value or "" for key, value in row.items()} for row in csv.DictReader(text.splitlines(), dialect=dialect)]


def normalize_meta_row(raw: dict[str, Any], source_file: Path) -> dict[str, str]:
    title = first_value(raw, "title")
    published_at = first_value(raw, "published_at")
    return {
        "title": title,
        "authors": first_value(raw, "authors"),
        "source": first_value(raw, "source"),
        "published_at": published_at,
        "year": str(extract_year(published_at)),
        "publication_type": first_value(raw, "publication_type"),
        "cited_count": str(parse_int(first_value(raw, "cited_count"))),
        "download_count": str(parse_int(first_value(raw, "download_count"))),
        "detail_url": first_value(raw, "detail_url"),
        "download_url": first_value(raw, "download_url"),
        "html_url": first_value(raw, "html_url"),
        "ai_read_url": first_value(raw, "ai_read_url"),
        "rank": first_value(raw, "rank"),
        "source_file": str(source_file),
    }


def load_export_metadata(project: str) -> tuple[dict[str, dict[str, str]], list[Path]]:
    export_dir = CNKI_EXPORTS / project
    if not export_dir.exists():
        return {}, []

    files = sorted(
        [path for path in export_dir.glob("*") if path.suffix.lower() in {".json", ".csv", ".tsv"}],
        key=lambda item: (0 if "current" in item.name else 1, -item.stat().st_mtime),
    )
    metadata: dict[str, dict[str, str]] = {}
    used_files: list[Path] = []

    for path in files:
        rows: list[dict[str, Any]]
        try:
            if path.suffix.lower() == ".json":
                data = json.loads(read_text(path))
                rows = data.get("rows", data) if isinstance(data, dict) else data
                if not isinstance(rows, list):
                    continue
            else:
                rows = parse_csv_like(path)
        except Exception:
            continue

        used_files.append(path)
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            meta = normalize_meta_row(raw, path)
            key = normalize_title(meta["title"])
            if not key:
                continue
            old = metadata.get(key)
            if old is None:
                metadata[key] = meta
                continue
            old_weight = parse_int(old.get("cited_count")) + parse_int(old.get("download_count"))
            new_weight = parse_int(meta.get("cited_count")) + parse_int(meta.get("download_count"))
            if new_weight >= old_weight:
                metadata[key] = meta
    return metadata, used_files


def infer_terms(project_root: Path) -> list[str]:
    terms: list[str] = []
    rq = project_root / "01_research_question.md"
    if rq.exists():
        text = read_text(rq)
        in_core = False
        for line in text.splitlines():
            if line.strip().startswith("## "):
                in_core = "Core Concepts" in line or "核心概念" in line
                continue
            if in_core and line.strip().startswith("- "):
                terms.append(line.strip()[2:].strip())
    plan = project_root / "literature" / "cnki_search_plan.md"
    if plan.exists():
        text = read_text(plan)
        for term in re.findall(r"主题\s*=\s*([^\s)）ORAND]+)", text):
            if term not in {"AND", "OR"}:
                terms.append(term)
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        term = clean(term)
        if term and term not in seen:
            unique.append(term)
            seen.add(term)
    return unique[:24]


def default_required_groups(terms: list[str]) -> list[list[str]]:
    library_terms = [term for term in terms if "图书" in term or "阅读推广" in term or "知识" in term]
    video_terms = [term for term in terms if "短视频" in term or "抖音" in term or "快手" in term or "视频" in term or "直播" in term]
    groups: list[list[str]] = []
    if library_terms:
        groups.append(library_terms[:8])
    if video_terms:
        groups.append(video_terms[:8])
    return groups


def ensure_profile(project: str, topic: str, explicit_profile: Path | None) -> tuple[dict[str, Any], Path, bool]:
    project_root = PROJECTS / project
    profile_path = explicit_profile or project_root / "literature" / "recommendation_profile.json"
    if profile_path.exists():
        with profile_path.open(encoding="utf-8") as handle:
            profile = json.load(handle)
        return profile, profile_path, False

    terms = infer_terms(project_root)
    profile = dict(DEFAULT_PROFILE)
    profile["project"] = project
    profile["topic"] = topic
    profile["include_terms"] = terms
    profile["required_term_groups"] = default_required_groups(terms)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return profile, profile_path, True


def load_state(project: str) -> tuple[dict[str, Any], Path]:
    path = PROJECTS / project / "literature" / "daily_learning_state.json"
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            return json.load(handle), path
    return {"project": project, "history": []}, path


def auto_stage(profile: dict[str, Any], state: dict[str, Any], current_date: str) -> str:
    history = [item for item in state.get("history", []) if item.get("primary") and item.get("date") != current_date]
    count = len(history)
    foundation_days = int(profile.get("foundation_days") or 5)
    review_days = int(profile.get("review_days") or 3)
    recent_days = int(profile.get("recent_days") or 4)
    if count < foundation_days:
        return "foundation_high_impact"
    if count < foundation_days + review_days:
        return "review_and_map"
    if count < foundation_days + review_days + recent_days:
        return "recent_important"
    return "method_model"


def history_keys(state: dict[str, Any], current_date: str) -> set[str]:
    keys: set[str] = set()
    for item in state.get("history", []):
        if item.get("date") == current_date:
            continue
        primary = item.get("primary")
        if primary:
            keys.add(primary)
        for key in item.get("companions", []) or []:
            if key:
                keys.add(key)
    return keys


def score_relevance(row: dict[str, str], profile: dict[str, Any]) -> tuple[float, list[str]]:
    content_blob = clean("\n".join([row.get("title", ""), row.get("core_findings", ""), row.get("target_journal_relevance", "")]))
    include_terms = [clean(item) for item in profile.get("include_terms", []) if clean(item)]
    exclude_terms = [clean(item) for item in profile.get("exclude_terms", []) if clean(item)]
    groups = profile.get("required_term_groups", []) or []

    hits = [term for term in include_terms if term and term in content_blob]
    group_hits = []
    for group in groups:
        group_terms = [clean(item) for item in group if clean(item)]
        group_hit = [term for term in group_terms if term in content_blob]
        if group_hit:
            group_hits.append(group_hit[0])

    score = min(70.0, 8.0 * len(hits))
    score += 15.0 * len(group_hits)
    if groups and len(group_hits) < len(groups):
        score -= 18.0 * (len(groups) - len(group_hits))

    negative_hits = [term for term in exclude_terms if term and term in content_blob]
    score -= 25.0 * len(negative_hits)
    score = max(-40.0, min(100.0, score))

    reasons: list[str] = []
    if hits:
        reasons.append("领域词命中: " + "、".join(hits[:6]))
    if group_hits:
        reasons.append("核心主题组覆盖: " + "、".join(group_hits[:4]))
    if negative_hits:
        reasons.append("排除词提醒: " + "、".join(negative_hits[:4]))
    return score, reasons


def score_source(source: str, profile: dict[str, Any]) -> tuple[float, str]:
    if any(item and item in source for item in profile.get("target_sources", [])):
        return 100.0, "目标刊/强相关来源"
    if any(item and item in source for item in profile.get("strong_sources", [])):
        return 80.0, "高质量图情来源"
    if any(item and item in source for item in profile.get("field_sources", [])):
        return 65.0, "图情领域来源"
    if "图书" in source or "情报" in source:
        return 55.0, "图情相关来源"
    return 25.0, "来源质量待人工判断"


def signal_score(title: str, terms: list[str], weight: float = 16.0) -> float:
    hits = [term for term in terms if term and term in title]
    return min(100.0, weight * len(hits))


def availability(row: dict[str, str], project: str) -> tuple[float, Path | None, Path | None, list[str]]:
    citekey = row.get("citekey", "")
    reader = PROJECTS / project / "literature" / "readers" / citekey / "paper.md"
    reader_path = reader if reader.exists() else None
    pdf_path = resolve_path(row.get("pdf_path", ""))
    reasons: list[str] = []
    score = 0.0
    if reader_path:
        score += 22.0
        reasons.append("已有 source-grounded reader")
    if pdf_path and pdf_path.exists():
        score += 12.0
        reasons.append("已有本地授权全文/转换 PDF")
    elif pdf_path:
        score += 4.0
        reasons.append("矩阵有全文路径但文件需核对")
    if row.get("note_path", "").strip():
        score += 6.0
        reasons.append("已有笔记路径")
    return min(40.0, score), reader_path, pdf_path, reasons


def candidate_score(
    row: dict[str, str],
    meta: dict[str, str],
    profile: dict[str, Any],
    project: str,
    stage: str,
    current_year: int,
    seen: set[str],
) -> Candidate | None:
    status = clean(row.get("read_status", ""))
    if status in BLOCKED_READ_STATUSES:
        return None

    cited = parse_int(meta.get("cited_count"))
    downloads = parse_int(meta.get("download_count"))
    year = extract_year(row.get("year", ""), meta.get("published_at", ""), meta.get("year", ""))
    title = row.get("title", "")
    source = row.get("source", "") or meta.get("source", "")

    impact = min(100.0, cited * 0.32 + math.log1p(downloads) * 5.2)
    relevance, relevance_reasons = score_relevance(row, profile)
    source_score, source_reason = score_source(source, profile)
    review_signal = signal_score(title, REVIEW_TERMS)
    method_signal = signal_score(title, METHOD_TERMS)
    recent_signal = 0.0
    if year:
        recent_signal = max(0.0, 100.0 - max(0, current_year - year) * 18.0)
    foundation_age = 18.0 if 2019 <= year <= 2021 else (10.0 if year else 0.0)
    availability_score, reader_path, pdf_path, availability_reasons = availability(row, project)

    read_adjustment = 0.0
    if status == "skimmed":
        read_adjustment -= 10.0
    elif status in {"metadata-only", "unread", ""}:
        read_adjustment += 4.0

    repetition_penalty = -80.0 if row.get("citekey") in seen else 0.0

    components = {
        "impact": impact,
        "relevance": relevance,
        "source": source_score,
        "review_signal": review_signal,
        "method_signal": method_signal,
        "recent_signal": recent_signal,
        "availability": availability_score,
        "foundation_age": foundation_age,
        "read_adjustment": read_adjustment,
        "repetition_penalty": repetition_penalty,
    }

    if stage == "review_and_map":
        score = (
            review_signal * 0.34
            + relevance * 0.24
            + impact * 0.16
            + source_score * 0.12
            + availability_score * 0.10
            + recent_signal * 0.04
        )
    elif stage == "recent_important":
        score = (
            recent_signal * 0.34
            + relevance * 0.23
            + impact * 0.20
            + source_score * 0.12
            + availability_score * 0.08
            + method_signal * 0.03
        )
    elif stage == "method_model":
        score = (
            method_signal * 0.34
            + relevance * 0.22
            + impact * 0.18
            + source_score * 0.11
            + availability_score * 0.10
            + recent_signal * 0.05
        )
    else:
        score = (
            impact * 0.36
            + relevance * 0.25
            + source_score * 0.16
            + availability_score * 0.10
            + foundation_age
        )

    score += read_adjustment + repetition_penalty

    reasons: list[str] = []
    if cited or downloads:
        reasons.append(f"CNKI 被引 {cited}，下载 {downloads}")
    reasons.extend(relevance_reasons)
    if source_reason:
        reasons.append(source_reason)
    if review_signal > 0:
        reasons.append("可用于现状/问题/策略地图")
    if method_signal > 0:
        reasons.append("有模型、实证或方法线索")
    if year >= current_year - 3 and year:
        reasons.append("近年文献")
    reasons.extend(availability_reasons)
    if status == "skimmed":
        reasons.append("已 skimmed，可升级为复盘式精读")
    if row.get("citekey") in seen:
        reasons.append("已在历史推荐中出现，默认降权")

    return Candidate(
        row=row,
        meta=meta,
        stage=stage,
        score=score,
        components=components,
        reasons=reasons,
        reader_path=reader_path,
        pdf_path=pdf_path,
    )


def rank_candidates(
    rows: list[dict[str, str]],
    metadata: dict[str, dict[str, str]],
    profile: dict[str, Any],
    project: str,
    stage: str,
    current_date: str,
    state: dict[str, Any],
) -> list[Candidate]:
    current_year = extract_year(current_date) or dt.date.today().year
    seen = history_keys(state, current_date)
    ranked: list[Candidate] = []
    for row in rows:
        meta = metadata.get(normalize_title(row.get("title", "")), {})
        candidate = candidate_score(row, meta, profile, project, stage, current_year, seen)
        if candidate:
            ranked.append(candidate)
    ranked.sort(
        key=lambda item: (
            item.score,
            item.components.get("impact", 0.0),
            item.components.get("relevance", 0.0),
            parse_int(item.meta.get("cited_count")),
        ),
        reverse=True,
    )
    return ranked


def reading_steps(stage: str) -> list[str]:
    if stage == "review_and_map":
        return [
            "先划出它如何定义研究对象、场景和问题边界。",
            "提取主题分类：服务对象、平台、传播指标、运营策略、证据类型。",
            "记录它遗漏了什么，尤其是平台指标和图书馆服务价值之间的缺口。",
            "把可复用的分类或概念补入 `03_literature_synthesis.md`。",
        ]
    if stage == "recent_important":
        return [
            "先判断这篇文献相对 2019-2021 年基础文献的新意在哪里。",
            "重点看平台、数据、用户行为、服务场景是否发生变化。",
            "对照已读基础文献，标出延续、修正或反驳之处。",
            "只把全文核验过的证据写进项目主张。",
        ]
    if stage == "method_model":
        return [
            "先抽取研究模型、变量、样本、指标和统计/分析方法。",
            "判断变量能否落到图书馆服务价值，而不只是平台互动量。",
            "记录可复用设计和不可复用风险，比如样本偏差、编码可靠性、因果限制。",
            "把方法启发写入后续研究设计或假设登记。",
        ]
    return [
        "先读题名、摘要/引言和结论，确认它为什么成为领域基础文献。",
        "再看研究对象、数据来源、指标和方法，判断证据强度。",
        "提取 3 个可复用概念或判断框架，以及 2 个明显局限。",
        "最后连接到你的问题：它帮助我们理解图书馆短视频的什么核心机制？",
    ]


def discussion_questions(stage: str, candidate: Candidate) -> list[str]:
    base = [
        "这篇文章真正解决的是图书馆服务问题、传播效果问题，还是平台运营问题？",
        "它把短视频效果测量成什么：观看、点赞、互动、阅读推广、服务触达，还是知识传播？",
        "它的证据是否足以支撑结论？哪些地方只是经验判断或策略建议？",
        "如果面向《图书情报工作》，它提示我们需要补强哪类图情领域贡献？",
    ]
    if stage == "foundation_high_impact":
        base.insert(1, "它为什么被引较多：理论框架、数据方法、实践问题，还是选题时机？")
    elif stage == "review_and_map":
        base.insert(1, "它能否帮我们搭建主题地图？有哪些分类维度可以保留？")
    elif stage == "recent_important":
        base.insert(1, "它相对早期文献的新变化是什么？这种变化是否足以改变研究问题？")
    elif stage == "method_model":
        base.insert(1, "它的方法设计能否被复用？复用前需要补哪些变量或验证步骤？")
    return base


def candidate_row(candidate: Candidate, rank: int) -> str:
    row = candidate.row
    meta = candidate.meta
    reader = "yes" if candidate.reader_path else "no"
    pdf = "yes" if candidate.pdf_path else "no"
    cited = parse_int(meta.get("cited_count"))
    downloads = parse_int(meta.get("download_count"))
    return (
        f"| {rank} | {candidate.score:.1f} | `{table_cell(candidate.citekey)}` | "
        f"{table_cell(row.get('year'))} | {table_cell(row.get('title'))} | "
        f"{table_cell(row.get('source'))} | {cited} | {downloads} | "
        f"{reader} | {pdf} | {table_cell(row.get('read_status'))} |"
    )


def command_hints(project: str, candidate: Candidate) -> list[str]:
    citekey = candidate.citekey
    hints = [f"make paper-brief CITEKEY={citekey}", f"make insight-bank PROJECT={project} CITEKEY={citekey}"]
    if candidate.reader_path:
        return hints
    if candidate.pdf_path and candidate.pdf_path.suffix.lower() == ".caj":
        hints.append(f"make caj-convert PROJECT={project} CITEKEY={citekey} UPDATE=1 RUN_READER=1")
    elif candidate.pdf_path:
        hints.append(f"make paper-reader PROJECT={project} CITEKEY={citekey} PDF={rel(candidate.pdf_path)} UPDATE=1")
    return hints


def resource_hints(candidate: Candidate) -> list[str]:
    hints: list[str] = []
    if candidate.reader_path:
        hints.append(f"已可精读 reader: `{rel(candidate.reader_path)}`")
    if candidate.pdf_path:
        hints.append(f"本地全文: `{rel(candidate.pdf_path)}`")
    if not hints:
        hints.append("如需精读：先通过授权 CNKI/机构渠道下载全文，再运行 `make paper-reader`。")
    return hints


def render_report(
    project: str,
    topic: str,
    current_date: str,
    stage: str,
    rows: list[dict[str, str]],
    ranked: list[Candidate],
    export_files: list[Path],
    profile_path: Path,
    profile_created: bool,
    state_path: Path,
    companion_count: int,
) -> str:
    primary = ranked[0] if ranked else None
    companions = ranked[1 : 1 + companion_count]
    queue = ranked[: min(12, len(ranked))]

    lines = [
        f"# CNKI 每日论文推荐 - {topic or project}",
        "",
        f"Date: {current_date}",
        f"Project: `{project}`",
        f"Stage: `{stage}` / {STAGE_LABELS.get(stage, stage)}",
        f"Stage logic: {STAGE_DESCRIPTIONS.get(stage, '')}",
        f"Candidate pool: {len(rows)} project-tagged CNKI rows",
        f"Profile: `{rel(profile_path)}`" + (" (created)" if profile_created else ""),
        f"State: `{rel(state_path)}`",
        "",
        "## 边界",
        "",
        "- 这是每日学习推荐，不等同于全文核验。",
        "- `metadata-only`、`skimmed` 不能直接作为论文证据；真正写进论文前必须补足全文阅读和 source locator。",
        "- 原文只使用你通过 CNKI/机构/图书馆合法取得的本地文件。",
        "",
    ]

    if export_files:
        lines.extend(["## 指标来源", ""])
        for path in export_files[:8]:
            lines.append(f"- `{rel(path)}`")
        if len(export_files) > 8:
            lines.append(f"- ... {len(export_files) - 8} more export files")
        lines.append("")

    if not primary:
        lines.extend(
            [
                "## 今日主读",
                "",
                "当前没有可推荐候选。请先导入 CNKI 元数据，或检查 `project_tags` 是否包含当前项目。",
                "",
            ]
        )
        return "\n".join(lines)

    row = primary.row
    meta = primary.meta
    lines.extend(
        [
            "## 今日主读",
            "",
            f"**{row.get('title')}**",
            "",
            f"- Citekey: `{primary.citekey}`",
            f"- 年份/来源: {row.get('year') or meta.get('year') or '未记录'} / {row.get('source') or meta.get('source') or '未记录'}",
            f"- 作者: {row.get('authors') or meta.get('authors') or '未记录'}",
            f"- CNKI 指标: 被引 {parse_int(meta.get('cited_count'))}，下载 {parse_int(meta.get('download_count'))}",
            f"- 阅读状态: `{row.get('read_status') or 'blank'}`",
            f"- Reader: `{rel(primary.reader_path)}`" if primary.reader_path else "- Reader: 未生成",
            f"- 本地全文: `{rel(primary.pdf_path)}`" if primary.pdf_path else "- 本地全文: 未记录",
            "",
            "### 为什么今天读它",
            "",
        ]
    )
    for reason in primary.reasons[:8]:
        lines.append(f"- {reason}")
    lines.extend(["", "### 今天怎么读", ""])
    for step in reading_steps(stage):
        lines.append(f"- {step}")
    lines.extend(["", "### 研讨问题", ""])
    for question in discussion_questions(stage, primary):
        lines.append(f"- {question}")
    lines.extend(["", "### 下一步命令", "", "```bash"])
    for hint in command_hints(project, primary):
        lines.append(hint)
    lines.extend(["```", "", "### 可用资源", ""])
    for hint in resource_hints(primary):
        lines.append(f"- {hint}")
    lines.append("")

    lines.extend(
        [
            "## 伴读队列",
            "",
            "| Rank | Score | Citekey | Year | Title | Source | Cited | Downloads | Reader | PDF | Read status |",
            "|---:|---:|---|---:|---|---|---:|---:|---|---|---|",
        ]
    )
    for idx, candidate in enumerate(companions, start=1):
        lines.append(candidate_row(candidate, idx))
    if not companions:
        lines.append("|  |  |  |  | 暂无 |  |  |  |  |  |  |")
    lines.extend(["", "## 后续候选池", ""])
    lines.extend(
        [
            "| Rank | Score | Citekey | Year | Title | Source | Cited | Downloads | Reader | PDF | Read status |",
            "|---:|---:|---|---:|---|---|---:|---:|---|---|---|",
        ]
    )
    for idx, candidate in enumerate(queue, start=1):
        lines.append(candidate_row(candidate, idx))

    lines.extend(
        [
            "",
            "## 今日记录动作",
            "",
            "- [ ] 读完后，把真实阅读状态只升级到实际达到的层级：`skimmed`、`human-read` 或 `verified`。",
            "- [ ] 把主读论文的创新点、局限性和可转化机会写入 `projects/<project>/literature/innovation_limitation_bank.md`。",
            "- [ ] 若讨论形成稳定判断，更新 `projects/<project>/03_literature_synthesis.md`。",
            "- [ ] 若用于论文主张，补 source locator，再运行 `make evidence-gate PROJECT=<project>`。",
            "",
        ]
    )
    return "\n".join(lines)


def update_state(
    state: dict[str, Any],
    state_path: Path,
    current_date: str,
    stage: str,
    primary: Candidate | None,
    companions: list[Candidate],
    output: Path,
) -> None:
    if primary is None:
        return
    entry = {
        "date": current_date,
        "stage": stage,
        "primary": primary.citekey,
        "companions": [item.citekey for item in companions],
        "output": rel(output),
        "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    history = [item for item in state.get("history", []) if item.get("date") != current_date]
    history.append(entry)
    state["history"] = sorted(history, key=lambda item: item.get("date", ""))
    state["last_updated"] = dt.datetime.now().isoformat(timespec="seconds")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a daily CNKI paper recommendation and learning plan.")
    parser.add_argument("--project", required=True, help="Project slug used in literature_matrix project_tags.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--topic", default="", help="Human-readable topic.")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--stage", choices=["auto", *STAGE_ORDER], default="auto")
    parser.add_argument("--companions", type=int, default=3, help="Number of companion papers to list.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile", type=Path, help="Optional recommendation profile JSON path.")
    parser.add_argument("--no-update-state", action="store_true", help="Write report without updating daily recommendation history.")
    args = parser.parse_args()

    rows = load_matrix(args.matrix, args.project)
    metadata, export_files = load_export_metadata(args.project)
    profile, profile_path, profile_created = ensure_profile(args.project, args.topic, args.profile)
    if args.topic and not profile.get("topic"):
        profile["topic"] = args.topic
    state, state_path = load_state(args.project)
    stage = auto_stage(profile, state, args.date) if args.stage == "auto" else args.stage
    ranked = rank_candidates(rows, metadata, profile, args.project, stage, args.date, state)

    output = args.output
    if output is None:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        output = OUT_DIR / f"{args.date}-{args.project}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(
        project=args.project,
        topic=args.topic or profile.get("topic", ""),
        current_date=args.date,
        stage=stage,
        rows=rows,
        ranked=ranked,
        export_files=export_files,
        profile_path=profile_path,
        profile_created=profile_created,
        state_path=state_path,
        companion_count=max(0, args.companions),
    )
    output.write_text(report, encoding="utf-8")

    if not args.no_update_state:
        update_state(state, state_path, args.date, stage, ranked[0] if ranked else None, ranked[1 : 1 + max(0, args.companions)], output)

    print(f"Wrote CNKI daily recommendation: {output}")
    print(f"Stage: {stage}")
    print(f"Candidates: {len(ranked)}")
    if ranked:
        print(f"Primary: {ranked[0].citekey} | {ranked[0].title}")
    if profile_created:
        print(f"Created recommendation profile: {profile_path}")
    if not args.no_update_state and ranked:
        print(f"Updated recommendation state: {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
