#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "library" / "literature_matrix.csv"
CNKI_DIR = ROOT / "library" / "cnki_exports"
REPORT_DIR = CNKI_DIR / "import_reports"

MATRIX_FIELDS = [
    "citekey",
    "title",
    "year",
    "authors",
    "doi",
    "source",
    "source_database",
    "language",
    "publication_type",
    "cssci_status",
    "project_tags",
    "theory",
    "methods",
    "data",
    "core_findings",
    "limitations",
    "usable_quotes",
    "chinese_reference_translation",
    "target_journal_relevance",
    "read_status",
    "note_path",
    "pdf_path",
]

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

COLUMN_ALIASES = {
    "title": {
        "title",
        "ti",
        "t1",
        "题名",
        "篇名",
        "标题",
        "文献题名",
        "论文题名",
        "中文题名",
    },
    "authors": {
        "author",
        "authors",
        "au",
        "a1",
        "作者",
        "著者",
        "责任者",
    },
    "year": {
        "year",
        "py",
        "y1",
        "出版年",
        "发表时间",
        "发表日期",
        "年",
        "年份",
        "日期",
    },
    "doi": {"doi", "do", "数字对象唯一标识符"},
    "source": {
        "source",
        "journal",
        "jo",
        "jf",
        "t2",
        "来源",
        "刊名",
        "期刊",
        "期刊名称",
        "出版物",
        "出版物名称",
        "文献来源",
    },
    "publication_type": {
        "type",
        "ty",
        "文献类型",
        "类型",
        "资源类型",
        "publicationtype",
    },
    "keywords": {"keyword", "keywords", "kw", "关键词", "主题词"},
    "abstract": {"abstract", "ab", "摘要", "内容摘要"},
    "cssci_status": {
        "cssci",
        "来源类别",
        "期刊级别",
        "收录",
        "核心期刊",
        "核心",
        "基金",
    },
}


def normalize_key(value: str) -> str:
    return re.sub(r"[\s_\-:：()（）\[\]【】]+", "", value.strip().lower())


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16", "utf-16le", "utf-16be"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def detect_csv_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        return csv.excel


def field_value(row: dict[str, str], field: str) -> str:
    aliases = {normalize_key(item) for item in COLUMN_ALIASES[field]}
    for key, value in row.items():
        if normalize_key(key) in aliases:
            return str(value or "").strip()
    return ""


def normalize_authors(value: str) -> str:
    value = value.strip()
    value = value.replace("\r", " ").replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.replace("；", ";").replace("，", ";").replace("、", ";")
    value = re.sub(r";+", ";", value)
    return value.strip(" ;")


def extract_year(value: str) -> str:
    match = re.search(r"(19|20)\d{2}", value or "")
    return match.group(0) if match else ""


def detect_language(title: str, abstract: str = "") -> str:
    return "zh-CN" if CJK_RE.search(title + abstract) else ""


def make_citekey(title: str, year: str, authors: str) -> str:
    digest = hashlib.sha1(f"{title}|{year}|{authors}".encode("utf-8")).hexdigest()[:10]
    return f"cnki_{year or 'nodate'}_{digest}"


def normalize_publication_type(value: str) -> str:
    value = value.strip()
    mapping = {
        "JOUR": "journal-article",
        "Journal Article": "journal-article",
        "期刊": "journal-article",
        "学位论文": "thesis",
        "会议": "conference-paper",
        "报纸": "newspaper-article",
        "图书": "book",
    }
    return mapping.get(value, value)


def row_to_matrix(row: dict[str, str], tag: str) -> dict[str, str]:
    title = field_value(row, "title")
    authors = normalize_authors(field_value(row, "authors"))
    year = extract_year(field_value(row, "year"))
    abstract = field_value(row, "abstract")
    keywords = field_value(row, "keywords")
    core_findings = abstract
    if keywords:
        core_findings = f"{abstract}\n关键词：{keywords}".strip()
    return {
        "citekey": make_citekey(title, year, authors),
        "title": title,
        "year": year,
        "authors": authors,
        "doi": field_value(row, "doi"),
        "source": field_value(row, "source"),
        "source_database": "CNKI",
        "language": detect_language(title, abstract),
        "publication_type": normalize_publication_type(field_value(row, "publication_type")),
        "cssci_status": field_value(row, "cssci_status"),
        "project_tags": tag,
        "theory": "",
        "methods": "",
        "data": "",
        "core_findings": core_findings,
        "limitations": "",
        "usable_quotes": "",
        "chinese_reference_translation": "",
        "target_journal_relevance": "",
        "read_status": "metadata-only",
        "note_path": "",
        "pdf_path": "",
    }


def parse_csv_like(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    dialect = detect_csv_dialect(text[:4096])
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    return [{key or "": value or "" for key, value in row.items()} for row in reader]


def parse_excel(path: Path) -> list[dict[str, str]]:
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            f"{path.name} is an Excel file, but pandas/openpyxl is not available. "
            "Install requirements.txt or export from CNKI as CSV/RIS/EndNote text."
        ) from exc
    try:
        frame = pd.read_excel(path, dtype=str)
    except ImportError as exc:
        raise RuntimeError(
            f"{path.name} could not be read because the Excel backend is missing. "
            "For .xlsx install openpyxl; for .xls install xlrd; or export as CSV/RIS/EndNote text."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Could not parse Excel export {path.name}: {exc}") from exc
    frame = frame.fillna("")
    return [{str(key): str(value).strip() for key, value in row.items()} for row in frame.to_dict(orient="records")]


def parse_ris(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        match = re.match(r"^([A-Z0-9]{2})\s*-\s*(.*)$", line)
        if not match:
            match = re.match(r"^%([A-Z0-9])\s*(.*)$", line)
        if not match:
            continue
        tag, value = match.group(1), match.group(2).strip()
        if tag == "ER":
            if current:
                records.append(current)
                current = {}
            continue
        current.setdefault(tag, []).append(value)
    if current:
        records.append(current)

    rows: list[dict[str, str]] = []
    for record in records:
        title = first(record, ["TI", "T1", "T"])
        authors = ";".join(record.get("AU", []) + record.get("A1", []) + record.get("A", []))
        rows.append(
            {
                "TY": first(record, ["TY", "0"]),
                "TI": title,
                "AU": authors,
                "PY": first(record, ["PY", "Y1", "D"]),
                "DO": first(record, ["DO", "R"]),
                "JO": first(record, ["JO", "JF", "T2", "J"]),
                "KW": ";".join(record.get("KW", []) + record.get("K", [])),
                "AB": first(record, ["AB", "N2", "X"]),
            }
        )
    return rows


def first(record: dict[str, list[str]], keys: list[str]) -> str:
    for key in keys:
        values = record.get(key)
        if values:
            return values[0]
    return ""


def parse_file(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        return parse_csv_like(path)
    if suffix in {".ris", ".txt", ".enw"}:
        text = read_text(path)
        if re.search(r"(^TY\s*-|^%0\s+)", text, flags=re.MULTILINE):
            return parse_ris(path)
        return parse_csv_like(path)
    if suffix in {".xlsx", ".xls"}:
        return parse_excel(path)
    raise RuntimeError(f"Unsupported CNKI export format: {path.suffix}")


def load_existing(path: Path) -> tuple[set[str], set[tuple[str, str]]]:
    citekeys: set[str] = set()
    title_years: set[tuple[str, str]] = set()
    if not path.exists():
        return citekeys, title_years
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            citekey = row.get("citekey", "")
            title = row.get("title", "").strip()
            year = row.get("year", "").strip()
            if citekey:
                citekeys.add(citekey)
            if title:
                title_years.add((title, year))
    return citekeys, title_years


def ensure_matrix() -> None:
    MATRIX.parent.mkdir(parents=True, exist_ok=True)
    if not MATRIX.exists():
        with MATRIX.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=MATRIX_FIELDS).writeheader()


def render_report(source_files: list[Path], imported: list[dict[str, str]], skipped: list[tuple[str, str]], dry_run: bool) -> str:
    lines = [
        "# CNKI Import Report",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Mode: {'dry-run' if dry_run else 'apply'}",
        "",
        "## Source Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in source_files)
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Imported rows: {len(imported)}",
            f"- Skipped rows: {len(skipped)}",
            "",
            "## Imported",
            "",
        ]
    )
    if imported:
        lines.extend(["| citekey | year | title | source |", "|---|---:|---|---|"])
        for row in imported[:200]:
            lines.append(f"| `{row['citekey']}` | {row['year']} | {row['title']} | {row['source']} |")
        if len(imported) > 200:
            lines.append(f"| ... | ... | {len(imported) - 200} more rows omitted | ... |")
    else:
        lines.append("- None.")
    lines.extend(["", "## Skipped", ""])
    if skipped:
        lines.extend(["| Title | Reason |", "|---|---|"])
        for title, reason in skipped[:200]:
            lines.append(f"| {title or '(untitled)'} | {reason} |")
        if len(skipped) > 200:
            lines.append(f"| ... | {len(skipped) - 200} more rows omitted |")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Next Steps",
            "",
            "- Open `library/literature_matrix.csv` and fill CSSCI status, target-journal relevance, theory/method/data fields for key sources.",
            "- Add local PDF paths after downloading authorized full texts.",
            "- Mark `read_status` as `skimmed`, `human-read`, or `verified` only after actual reading.",
            "",
        ]
    )
    return "\n".join(lines)


def import_files(paths: list[Path], tag: str, dry_run: bool) -> tuple[list[dict[str, str]], list[tuple[str, str]]]:
    ensure_matrix()
    existing_keys, existing_title_years = load_existing(MATRIX)
    imported: list[dict[str, str]] = []
    skipped: list[tuple[str, str]] = []

    for path in paths:
        rows = parse_file(path)
        for raw_row in rows:
            row = row_to_matrix(raw_row, tag=tag)
            title = row["title"].strip()
            year = row["year"].strip()
            if not title:
                skipped.append((title, f"{path.name}: missing title"))
                continue
            if row["citekey"] in existing_keys or (title, year) in existing_title_years:
                skipped.append((title, "duplicate citekey or title/year"))
                continue
            existing_keys.add(row["citekey"])
            existing_title_years.add((title, year))
            imported.append(row)

    if imported and not dry_run:
        with MATRIX.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
            for row in imported:
                writer.writerow({field: row.get(field, "") for field in MATRIX_FIELDS})
    return imported, skipped


def expand_inputs(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        if item.is_dir():
            for suffix in ("*.csv", "*.tsv", "*.ris", "*.txt", "*.enw", "*.xlsx", "*.xls"):
                paths.extend(sorted(item.glob(suffix)))
        else:
            paths.append(item)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Import CNKI-exported metadata into library/literature_matrix.csv.")
    parser.add_argument("--input", nargs="+", type=Path, required=True, help="CNKI export files or directories")
    parser.add_argument("--tag", default="", help="Optional project tag")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without writing to literature_matrix.csv")
    parser.add_argument("--report", type=Path, help="Report path. Defaults to library/cnki_exports/import_reports/<timestamp>.md")
    args = parser.parse_args()

    paths = expand_inputs(args.input)
    if not paths:
        raise FileNotFoundError("No CNKI export files found.")
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)

    imported, skipped = import_files(paths, tag=args.tag, dry_run=args.dry_run)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = args.report or REPORT_DIR / f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-cnki-import.md"
    report_path.write_text(render_report(paths, imported, skipped, dry_run=args.dry_run), encoding="utf-8")

    print(f"Parsed files: {len(paths)}")
    print(f"Imported rows: {len(imported)}")
    print(f"Skipped rows: {len(skipped)}")
    print(f"Wrote report: {report_path}")
    if args.dry_run:
        print("Dry-run only; literature_matrix.csv was not modified.")
    else:
        print(f"Updated matrix: {MATRIX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
