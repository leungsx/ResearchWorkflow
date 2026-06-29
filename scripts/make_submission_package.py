#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import audit_references_gbt7714
import evidence_gate
import project_status


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def project_title(project: Path) -> str:
    metadata = project / "project.yaml"
    if metadata.exists():
        for raw_line in metadata.read_text(encoding="utf-8", errors="ignore").splitlines():
            if raw_line.startswith("title:"):
                return raw_line.split(":", 1)[1].strip().strip('"')
    paper = read_text(project / "manuscript" / "paper.md")
    for line in paper.splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
    return project.name.replace("_", " ").replace("-", " ").title()


def copy_if_exists(source: Path, dest: Path, copied: list[dict], missing: list[str]) -> None:
    if not source.exists():
        missing.append(source.relative_to(source.parents[2] if "projects" in source.parts else ROOT).as_posix())
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    copied.append({"source": str(source), "dest": str(dest), "bytes": dest.stat().st_size})


def copy_tree_files(source_dir: Path, dest_dir: Path, patterns: list[str], copied: list[dict]) -> int:
    if not source_dir.exists():
        return 0
    count = 0
    for pattern in patterns:
        for source in sorted(source_dir.glob(pattern)):
            if not source.is_file() or source.name.startswith("."):
                continue
            rel = source.relative_to(source_dir)
            dest = dest_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            copied.append({"source": str(source), "dest": str(dest), "bytes": dest.stat().st_size})
            count += 1
    return count


def extract_data_statement(project: Path) -> str:
    governance = read_text(project / "data" / "data_governance.md")
    if "Data availability statement draft:" in governance:
        after = governance.split("Data availability statement draft:", 1)[1]
        collected: list[str] = []
        for line in after.splitlines():
            if line.startswith("## "):
                break
            if line.strip():
                collected.append(line.rstrip())
        if collected:
            return "\n".join(collected).strip()

    paper = read_text(project / "manuscript" / "paper.md")
    marker = "# 数据可用性声明"
    if marker in paper:
        after = paper.split(marker, 1)[1]
        collected = []
        for line in after.splitlines():
            if line.startswith("# ") and collected:
                break
            if line.strip():
                collected.append(line.rstrip())
        meaningful = "\n".join(collected).strip()
        if meaningful and "本研究数据可用性说明：" not in meaningful:
            return meaningful

    return "待补充：请根据数据是否可共享，说明仓储链接/DOI/CSTR，或说明隐私、保密、第三方权益、伦理限制，或说明未产生新数据。"


def render_cover_letter(project: Path) -> str:
    title = project_title(project)
    today = dt.date.today().isoformat()
    return "\n".join(
        [
            "# 投稿信草稿",
            "",
            f"日期：{today}",
            "",
            "尊敬的《图书情报工作》编辑部：",
            "",
            f"现提交题为《{title}》的稿件，拟投贵刊。文章类型、栏目方向和选题契合度请以 `target_journal.md` 中的最终填写内容为准。",
            "",
            "本文的核心问题、主要发现和图书情报领域贡献请在正式投稿前补充为 2-3 句具体表述，避免空泛介绍。",
            "",
            "作者确认：稿件未一稿多投；所有作者已知晓并同意投稿；数据、图表、AI 使用和作者贡献说明已按投稿检查清单完成核查。",
            "",
            "此致",
            "",
            "敬礼！",
            "",
            "作者：",
            "单位：",
            "联系方式：",
            "",
        ]
    )


def render_readiness_snapshot(
    project: Path,
    package_dir: Path,
    citation_report_path: Path,
    evidence_report_path: Path,
    missing: list[str],
    evidence_summary: dict[str, int | str],
) -> str:
    required = [
        ("主文稿", project / "manuscript" / "paper.md"),
        ("目标期刊说明", project / "manuscript" / "target_journal.md"),
        ("投稿检查清单", project / "manuscript" / "submission_checklist_tushuqingbaogongzuo.md"),
        ("引用审计", citation_report_path),
        ("AI 使用披露", project / "manuscript" / "ai_usage_disclosure.md"),
        ("数据治理", project / "data" / "data_governance.md"),
        ("数据字典", project / "data" / "data_dictionary.md"),
        ("主张证据映射", project / "07_claim_evidence_map.md"),
        ("证据门禁", evidence_report_path),
        ("Material Passport", project / "passport" / "material_passport.json"),
    ]

    lines = [
        "# Submission Readiness Snapshot",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Project: `{project.name}`",
        f"Package: `{package_dir}`",
        "",
        "## Core Files",
        "",
        "| Item | Status | Path |",
        "|---|---|---|",
    ]
    for label, path in required:
        if not path.exists():
            status = "MISSING"
        elif project_status.meaningful_text(path):
            status = "FILLED"
        else:
            status = "STUB"
        lines.append(f"| {label} | {status} | `{path.relative_to(project) if path.is_relative_to(project) else path}` |")

    final_figures = project_status.count_files(project / "figures" / "final", ["*.png", "*.pdf", "*.svg"])
    figure_specs = project_status.count_files(project / "figures" / "specs", ["*.md"])
    packages = project_status.count_dirs(project / "submission_package", ["*"])
    lines.extend(
        [
            "",
            "## Materials",
            "",
            f"- Final figures: {final_figures}",
            f"- Figure specs: {figure_specs}",
            f"- Existing submission package entries: {packages}",
            f"- Evidence gate: {evidence_summary['status']} (ERROR={evidence_summary['ERROR']}, WARN={evidence_summary['WARN']})",
            "",
            "## Missing During Package Build",
            "",
        ]
    )
    if missing:
        lines.extend(f"- `{item}`" for item in missing)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Pre-Submission Reminders",
            "",
            "- Re-check the latest official journal template before upload.",
            "- Do not include raw private or sensitive data in the submission package.",
            "- Verify every cited source supports the local claim, not only the topic.",
            "- Complete copyright, confidentiality review, and any downloaded journal forms outside this generated package.",
            "",
        ]
    )
    return "\n".join(lines)


def write_checksums(package_dir: Path) -> None:
    rows = []
    for path in sorted(package_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"checksums.csv", "package_manifest.json"}:
            continue
        rows.append(
            {
                "path": path.relative_to(package_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    with (package_dir / "checksums.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)


def maybe_make_docx(project: Path, package_dir: Path, no_docx: bool) -> str:
    if no_docx:
        return "DOCX generation skipped by --no-docx."
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return "Pandoc not found in PATH; DOCX not generated."
    source = project / "manuscript" / "paper.md"
    if not source.exists():
        return "Manuscript not found; DOCX not generated."
    output = package_dir / "main_manuscript.docx"
    command = [pandoc, str(source), "-o", str(output)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    log = [
        f"Command: {' '.join(command)}",
        f"Return code: {completed.returncode}",
        "",
        "STDOUT:",
        completed.stdout.strip(),
        "",
        "STDERR:",
        completed.stderr.strip(),
        "",
    ]
    (package_dir / "conversion_log.txt").write_text("\n".join(log), encoding="utf-8")
    if completed.returncode == 0 and output.exists():
        return f"DOCX generated: {output.name}"
    return "Pandoc ran but DOCX generation failed; see conversion_log.txt."


def build_package(project: Path, timestamp: str, no_docx: bool) -> tuple[Path, dict[str, int | str], int]:
    package_dir = project / "submission_package" / timestamp
    package_dir.mkdir(parents=True, exist_ok=False)

    copied: list[dict] = []
    missing: list[str] = []

    report, citation_issues = audit_references_gbt7714.audit(project, None, None)
    citation_report = project / "manuscript" / "citation_audit_gbt7714.md"
    citation_report.write_text(report, encoding="utf-8")
    evidence_report, evidence_issues = evidence_gate.audit_project(project)
    evidence_summary = evidence_gate.summarize(evidence_issues)
    evidence_report_path = project / "manuscript" / "evidence_gate_report.md"
    evidence_report_path.write_text(evidence_report, encoding="utf-8")

    copy_if_exists(project / "manuscript" / "paper.md", package_dir / "main_manuscript.md", copied, missing)
    copy_if_exists(project / "manuscript" / "references.bib", package_dir / "references.bib", copied, missing)
    copy_if_exists(project / "manuscript" / "target_journal.md", package_dir / "target_journal.md", copied, missing)
    copy_if_exists(project / "manuscript" / "submission_checklist_tushuqingbaogongzuo.md", package_dir / "submission_checklist_tushuqingbaogongzuo.md", copied, missing)
    copy_if_exists(project / "manuscript" / "ai_usage_disclosure.md", package_dir / "ai_usage_disclosure.md", copied, missing)
    copy_if_exists(citation_report, package_dir / "citation_audit_gbt7714.md", copied, missing)
    copy_if_exists(evidence_report_path, package_dir / "integrity" / "evidence_gate_report.md", copied, missing)
    copy_if_exists(project / "data" / "data_dictionary.md", package_dir / "data" / "data_dictionary.md", copied, missing)
    copy_if_exists(project / "data" / "data_governance.md", package_dir / "data" / "data_governance.md", copied, missing)
    copy_if_exists(project / "07_claim_evidence_map.md", package_dir / "integrity" / "claim_evidence_map.md", copied, missing)
    copy_if_exists(project / "08_publication_readiness.md", package_dir / "integrity" / "publication_readiness.md", copied, missing)
    copy_if_exists(project / "passport" / "material_passport.json", package_dir / "integrity" / "material_passport.json", copied, missing)
    copy_if_exists(project / "passport" / "checksums.csv", package_dir / "integrity" / "project_checksums.csv", copied, missing)

    copy_tree_files(project / "figures" / "final", package_dir / "figures" / "final", ["*.png", "*.pdf", "*.svg", "*.tif", "*.tiff"], copied)
    copy_tree_files(project / "figures" / "specs", package_dir / "figures" / "specs", ["*.md"], copied)

    (package_dir / "data_availability_statement.md").write_text(
        "# Data Availability Statement\n\n" + extract_data_statement(project) + "\n",
        encoding="utf-8",
    )
    (package_dir / "cover_letter_draft.md").write_text(render_cover_letter(project), encoding="utf-8")
    docx_status = maybe_make_docx(project, package_dir, no_docx=no_docx)

    readiness = render_readiness_snapshot(project, package_dir, citation_report, evidence_report_path, missing, evidence_summary)
    (package_dir / "submission_readiness_snapshot.md").write_text(readiness, encoding="utf-8")

    readme = "\n".join(
        [
            f"# Submission Package - {project.name}",
            "",
            f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
            "Target journal: 《图书情报工作》",
            "",
            "## Contents",
            "",
            "- `main_manuscript.md`: Markdown 主文稿。",
            "- `main_manuscript.docx`: Pandoc 生成的 DOCX，如果本机可用且转换成功。",
            "- `references.bib`: BibTeX 引用库。",
            "- `citation_audit_gbt7714.md`: GB/T 7714 与中文参考文献英译检查报告。",
            "- `integrity/evidence_gate_report.md`: 证据阅读状态和 source locator 门禁报告。",
            "- `submission_checklist_tushuqingbaogongzuo.md`: 投稿检查清单。",
            "- `data_availability_statement.md`: 数据可用性说明草稿。",
            "- `ai_usage_disclosure.md`: AI 使用披露。",
            "- `figures/`: 最终图和图件 specs。",
            "- `integrity/`: 主张证据映射、readiness、Material Passport。",
            "",
            "## Conversion",
            "",
            f"- {docx_status}",
            "",
            "## Caution",
            "",
            "- This package intentionally excludes raw data.",
            "- Before upload, verify the latest official journal template and any copyright/confidentiality forms.",
            "",
        ]
    )
    (package_dir / "README.md").write_text(readme, encoding="utf-8")

    write_checksums(package_dir)
    manifest = {
        "schema": "ResearchWorkflow.SubmissionPackage.v1",
        "project": project.name,
        "target_journal": "图书情报工作",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "package_dir": str(package_dir),
        "copied_files": copied,
        "missing_inputs": missing,
        "docx_status": docx_status,
        "citation_error_count": sum(1 for issue in citation_issues if issue.severity == "ERROR"),
        "evidence_gate": evidence_summary,
    }
    (package_dir / "package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_checksums(package_dir)
    citation_error_count = sum(1 for issue in citation_issues if issue.severity == "ERROR")
    return package_dir, evidence_summary, citation_error_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a 《图书情报工作》 submission package for a project.")
    parser.add_argument("--project", required=True, help="Project slug under projects/")
    parser.add_argument("--timestamp", help="Package id. Defaults to YYYYMMDD-HHMMSS.")
    parser.add_argument("--no-docx", action="store_true", help="Skip Pandoc DOCX generation.")
    parser.add_argument("--strict", action="store_true", help="Exit 2 when citation or evidence ERROR issues are found.")
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(project)
    timestamp = args.timestamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    package_dir, evidence_summary, citation_error_count = build_package(project, timestamp=timestamp, no_docx=args.no_docx)
    print(f"Wrote submission package: {package_dir}")
    print(f"Open readiness snapshot: {package_dir / 'submission_readiness_snapshot.md'}")
    if args.strict and (citation_error_count or evidence_summary["ERROR"]):
        print("Strict mode failed: citation or evidence ERROR issues remain.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
