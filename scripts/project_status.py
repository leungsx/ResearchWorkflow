#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import evidence_gate


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"


REQUIRED_FILES = [
    ("Research question", "01_research_question.md"),
    ("Methodology", "02_methodology.md"),
    ("Data dictionary", "data/data_dictionary.md"),
    ("Data governance", "data/data_governance.md"),
    ("Literature synthesis", "03_literature_synthesis.md"),
    ("Experiment plan", "04_experiment_plan.md"),
    ("Hypothesis registry", "05_hypothesis_registry.md"),
    ("Result interpretation", "06_result_interpretation.md"),
    ("Claim-evidence map", "07_claim_evidence_map.md"),
    ("Publication readiness", "08_publication_readiness.md"),
    ("Target journal", "manuscript/target_journal.md"),
    ("Terminology ledger", "manuscript/terminology_ledger.md"),
    ("Manuscript", "manuscript/paper.md"),
    ("References", "manuscript/references.bib"),
    ("AI usage disclosure", "manuscript/ai_usage_disclosure.md"),
    ("Submission checklist", "manuscript/submission_checklist_tushuqingbaogongzuo.md"),
]


def meaningful_text(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    ignored_prefixes = (
        "#",
        "---",
        "title:",
        "author:",
        "bibliography:",
        "target-journal:",
        "language:",
        "Project:",
        "Project slug:",
        "Project folder:",
        "Dashboard:",
        "- Status: draft",
        "- Next action:",
        "- Stage: scoping",
        "- Blockers:",
        "- Origin:",
        "- Mechanism:",
        "- What would support it:",
        "- What would contradict it:",
        "- Data needed:",
        "- Method:",
        "- Risks:",
        "- Verdict:",
        "- Confidence:",
        "- Effect size:",
        "- Confidence interval:",
        "- P-value:",
        "- Assumptions checked:",
        "- Multiple comparisons:",
        "- Claim:",
        "- Evidence:",
        "- Strength:",
        "- Limitations:",
        "- Linked hypothesis:",
        "- Linked result:",
        "- Linked literature:",
        "- Figure/table:",
        "- What not to overclaim:",
        "- Total score:",
        "- Ready for:",
        "- Blocking issues:",
        "- Highest-leverage next action:",
        "- Journal:",
        "- Decision type:",
        "- Deadline:",
        "- Overall posture:",
        "- Major risks:",
        "- Points to accept:",
        "- Points to clarify:",
        "- Points to respectfully disagree with:",
        "- New experiments / analyses needed:",
        "- Package readiness:",
        "- Blocking missing information:",
        "- `0`:",
        "- `1`:",
        "- `2`:",
        "- [ ]",
        "- Article orientation:",
        "- Topic-fit signal:",
        "- Why this paper belongs",
        "- Practical or theoretical contribution:",
        "- Main audience:",
        "- Chinese structured abstract required:",
        "- Long English abstract required:",
        "- Chinese references need",
        "- Chinese and English titles",
        "- Data availability statement:",
        "- AI use disclosure:",
        "- Authorship constraints checked:",
        "- Map compliance needed:",
        "- Journal home:",
        "- Submission system:",
        "- Data submission:",
        "- Dataset name:",
        "- Source / collection method:",
        "- Time range:",
        "- Inclusion criteria:",
        "- Exclusion criteria:",
        "- Processing script:",
        "- Version:",
        "- Shareable:",
        "- Repository:",
        "- DOI / CSTR / URL:",
        "- If not shareable",
        "- Public / restricted",
        "- Contains personal information:",
        "- Contains institutional confidential information:",
        "- Third-party rights involved:",
        "- Data source:",
        "- Authorization / license:",
        "- Ethical review needed:",
        "- Consent needed:",
        "- Raw data location:",
        "- Processed data location:",
        "- Scripts:",
        "- De-identification steps:",
        "- Backup:",
        "- Reason:",
        "- Data availability statement draft:",
        "- AI tools used on data:",
        "- Tool:",
        "- Input data class:",
        "- Output type:",
        "- Risk and mitigation:",
        "- 工具名称：",
        "- 使用过程：",
        "- 作用和贡献：",
        "- 人工核查方式：",
        "- AI is not listed",
        "- AI-generated content is not cited",
        "- All factual claims",
        "作者姓名",
        "作者单位名称",
        "摘要：",
        "[目的/意义]",
        "[方法/过程]",
        "[结果/结论]",
        "[Purpose/Significance]",
        "[Method/Process]",
        "[Result/Conclusion]",
        "[Innovation/Value]",
        "[Insufficient/Improvement]",
        "关键词：关键词",
        "中图分类号：",
        "本研究数据可用性说明：",
        "本研究是否使用 AI 工具及其用途：",
        "作者1：",
        "作者2：",
        "```",
        "# Python",
        "# R",
        "# MATLAB",
        "Use this file before",
        "Score conservatively",
        "A weak score should",
        "Build this before",
        "Use one canonical",
        "Record substantive manuscript polishing",
        "This keeps wording changes",
        "Create one Markdown spec",
        "Do this before",
        "Use this folder",
        "Recommended package shape:",
        "Minimum expectations:",
        "Do not treat this as a summary-only folder",
        "Use this for group meeting",
        "Use this before drafting",
        "Keep editor instructions",
        "Do not invent",
        "Missing results, statistics",
        "Default target journal:",
        "Profile:",
        "Use this checklist before",
        "Use this for any dataset",
        "Use this when the project includes",
        "Use this before analysis",
        "Use this file to record",
        "transparency. For",
        "collection or analysis",
        "vague concern.",
        "responses. Use one canonical",
        "cohort, material, or concept.",
        "separate from reviewer comments",
        "location or an explicit placeholder.",
    )
    ignored_exact = {
        "{{PROJECT_TITLE}}",
        "{{PROJECT_SLUG}}",
        "Leung",
        "draft",
        "supports / contradicts / inconclusive / artifact / exploratory",
        "-",
    }
    table_header_first_cells = {
        "Area",
        "Canonical term",
        "Date",
        "Panel",
        "ID",
        "Slide",
        "Asset",
        "Claim ID",
    }

    def meaningful_table_line(line: str) -> str:
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if not cells:
            return ""
        if all(not cell or set(cell) <= {"-", ":"} for cell in cells):
            return ""
        if cells[0] in table_header_first_cells:
            return ""
        if len(cells) >= 5 and cells[1] == "0" and not cells[3] and not cells[4]:
            return ""
        if cells[0] in {"A", "B", "C"} and all(not cell for cell in cells[1:]):
            return ""
        if (cells[0].startswith("E.") or cells[0].startswith("R")) and all(not cell for cell in cells[1:]):
            return ""
        content = [
            cell
            for cell in cells
            if cell and set(cell) > {"-", ":"} and cell not in {"0", "1", "2"}
        ]
        return " ".join(content)

    useful = []
    in_code = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not line or in_code:
            continue
        if line in ignored_exact:
            continue
        if any(line.startswith(prefix) for prefix in ignored_prefixes):
            continue
        if line.startswith("|"):
            table_text = meaningful_table_line(line)
            if table_text:
                useful.append(table_text)
            continue
        if "{{" in line and "}}" in line:
            continue
        useful.append(line)
    return sum(len(line) for line in useful) >= 80


def count_files(path: Path, patterns: list[str]) -> int:
    if not path.exists():
        return 0
    total = 0
    for pattern in patterns:
        total += len(
            [
                item
                for item in path.glob(pattern)
                if item.is_file()
                and not item.name.startswith(".")
                and item.name.lower() != "readme.md"
                and "template" not in item.stem.lower()
                and item.stem.lower() not in {"figure_spec", "paper2ppt_plan"}
            ]
        )
    return total


def count_meaningful_files(path: Path, patterns: list[str]) -> int:
    if not path.exists():
        return 0
    total = 0
    for pattern in patterns:
        total += len(
            [
                item
                for item in path.glob(pattern)
                if item.is_file()
                and not item.name.startswith(".")
                and item.name.lower() != "readme.md"
                and "template" not in item.stem.lower()
                and item.stem.lower() not in {"figure_spec", "paper2ppt_plan"}
                and meaningful_text(item)
            ]
        )
    return total


def count_dirs(path: Path, patterns: list[str]) -> int:
    if not path.exists():
        return 0
    total = 0
    for pattern in patterns:
        total += len([item for item in path.glob(pattern) if item.is_dir() and not item.name.startswith(".")])
    return total


def latest_run(project: Path) -> Path | None:
    run_root = project / "passport" / "runs"
    if not run_root.exists():
        return None
    runs = sorted([p for p in run_root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0] if runs else None


def next_actions(project: Path) -> list[str]:
    actions = []
    _report, evidence_issues = evidence_gate.audit_project(project)
    evidence_summary = evidence_gate.summarize(evidence_issues)
    if evidence_summary["ERROR"]:
        actions.append("先修复证据门禁 ERROR：metadata-only、abstract-only、AI 摘要或未读文献不能支撑正文/claim map；需要合法全文、source locator，并标记 `human-read` 或 `verified`。")
    elif evidence_summary["WARN"]:
        actions.append("检查证据门禁 WARN：被项目材料引用的文献需要补全文阅读状态、reader/note/PDF 路径，避免后续写作误用。")
    if not meaningful_text(project / "01_research_question.md"):
        actions.append("先把 `01_research_question.md` 中的 Research Question、Scope、Expected Contribution 写清楚。")
    if not meaningful_text(project / "03_literature_synthesis.md"):
        actions.append("把核心文献放进 `03_literature_synthesis.md`，至少形成理论、方法、证据三个小节。")
    if count_files(project / "data" / "processed", ["*"]) == 0 and not meaningful_text(project / "04_experiment_plan.md"):
        actions.append("补齐 `04_experiment_plan.md`，明确输入、命令、输出和验证规则。")
    if (count_files(project / "data" / "raw", ["*"]) > 0 or count_files(project / "data" / "processed", ["*"]) > 0) and not meaningful_text(project / "data" / "data_dictionary.md"):
        actions.append("已有数据文件，下一步应补齐 `data/data_dictionary.md`，说明字段含义、来源、缺失值和可共享性。")
    if (count_files(project / "data" / "raw", ["*"]) > 0 or count_files(project / "data" / "processed", ["*"]) > 0) and not meaningful_text(project / "data" / "data_governance.md"):
        actions.append("已有数据文件，投稿前应补齐 `data/data_governance.md`，记录权限、隐私、共享和数据可用性声明。")
    if meaningful_text(project / "04_experiment_plan.md") and not meaningful_text(project / "05_hypothesis_registry.md"):
        actions.append("把要验证的猜想写进 `05_hypothesis_registry.md`，避免实验和研究问题脱节。")
    if latest_run(project) and not meaningful_text(project / "06_result_interpretation.md"):
        actions.append("已有实验运行记录，下一步应更新 `06_result_interpretation.md`，判断结果支持、反驳还是无法判断猜想。")
    if meaningful_text(project / "06_result_interpretation.md") and not meaningful_text(project / "07_claim_evidence_map.md"):
        actions.append("把可写入论文的结果整理进 `07_claim_evidence_map.md`，并标注证据强度和风险。")
    if meaningful_text(project / "manuscript" / "paper.md") and not meaningful_text(project / "manuscript" / "terminology_ledger.md"):
        actions.append("在润色或投稿前补齐 `manuscript/terminology_ledger.md`，锁定术语、缩写、数据集、指标和单位。")
    if not meaningful_text(project / "manuscript" / "target_journal.md"):
        actions.append("补齐 `manuscript/target_journal.md`：明确文章类型、选题契合点、图情领域贡献和《图书情报工作》投稿约束。")
    if count_files(project / "figures" / "final", ["*.png", "*.pdf", "*.svg"]) > 0 and count_files(project / "figures" / "specs", ["*.md"]) == 0:
        actions.append("已有最终图，但缺少 `figures/specs/*.md` 图件合同：核心结论、证据链、数据/脚本、统计、导出和 QA 都要写清楚。")
    if meaningful_text(project / "07_claim_evidence_map.md") and not meaningful_text(project / "08_publication_readiness.md"):
        actions.append("更新 `08_publication_readiness.md`，评估 RQ、文献、实验、图件、写作和完整性短板。")
    if meaningful_text(project / "manuscript" / "paper.md") and not meaningful_text(project / "manuscript" / "submission_checklist_tushuqingbaogongzuo.md"):
        actions.append("投稿前逐项完成 `manuscript/submission_checklist_tushuqingbaogongzuo.md`，特别是结构化摘要、长英文摘要、GB/T 7714、数据可用性和 AI 披露。")
    if meaningful_text(project / "manuscript" / "paper.md") and not meaningful_text(project / "manuscript" / "ai_usage_disclosure.md"):
        actions.append("投稿前补齐 `manuscript/ai_usage_disclosure.md`，记录 AI 在检索、分析、绘图、代码、翻译或润色中的使用。")
    if meaningful_text(project / "manuscript" / "paper.md") and not meaningful_text(project / "manuscript" / "citation_audit_gbt7714.md"):
        actions.append("运行 `make citation-audit PROJECT=<slug>`，检查 GB/T 7714、正文-参考文献对应关系和中文参考文献英译信息。")
    if meaningful_text(project / "manuscript" / "paper.md") and count_dirs(project / "submission_package", ["*"]) == 0:
        actions.append("投稿前运行 `make submission-package PROJECT=<slug>`，生成主文稿、引用审计、数据/AI 声明、图件和完整性材料的投稿包。")
    if not (project / "passport" / "material_passport.json").exists():
        actions.append("运行 `make passport PROJECT=<slug>` 生成 Material Passport。")
    if not actions:
        actions.append("当前基础材料齐全；下一步可以做引用核查、图表复现或论文结构审阅。")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Show a project status dashboard.")
    parser.add_argument("--project", required=True, help="Project slug")
    args = parser.parse_args()

    project = PROJECTS / args.project
    if not project.exists():
        raise FileNotFoundError(f"Project not found: {project}")

    print(f"# Project Status: {args.project}\n")
    print(f"Path: {project}\n")
    print("## Core Documents")
    for label, rel in REQUIRED_FILES:
        path = project / rel
        if not path.exists():
            status = "MISSING"
        elif meaningful_text(path):
            status = "FILLED"
        else:
            status = "STUB"
        print(f"- {status:<7} {label}: {rel}")

    print("\n## Materials")
    print(f"- Raw data files: {count_files(project / 'data' / 'raw', ['*'])}")
    print(f"- Processed data files: {count_files(project / 'data' / 'processed', ['*'])}")
    print(f"- Data dictionaries: {count_meaningful_files(project / 'data', ['data_dictionary.md'])}")
    print(f"- Data governance files: {count_meaningful_files(project / 'data', ['data_governance.md'])}")
    print(f"- Final figures: {count_files(project / 'figures' / 'final', ['*.png', '*.pdf', '*.svg'])}")
    print(f"- Figure specs: {count_files(project / 'figures' / 'specs', ['*.md'])}")
    print(f"- Reader packages: {count_files(project / 'literature' / 'readers', ['*/paper.md'])}")
    workbench = project / "literature" / "literature_review_workbench.md"
    if workbench.exists():
        workbench_status = "filled" if meaningful_text(workbench) else "stub"
    else:
        workbench_status = "missing"
    print(f"- Literature review workbench: {workbench_status}")
    print(f"- Presentation decks: {count_files(project / 'presentations', ['**/*.pptx'])}")
    print(f"- Review response trackers: {count_meaningful_files(project / 'review_response', ['*.md'])}")
    print(f"- GB/T 7714 citation audits: {count_files(project / 'manuscript', ['citation_audit_gbt7714.md'])}")
    print(f"- Submission packages: {count_dirs(project / 'submission_package', ['*'])}")

    run = latest_run(project)
    if run:
        report = run / "run_report.json"
        if report.exists():
            data = json.loads(report.read_text(encoding="utf-8"))
            print(f"- Latest run: {run.name} ({data.get('status')}, return_code={data.get('return_code')})")
        else:
            print(f"- Latest run: {run.name}")
    else:
        print("- Latest run: none")

    passport = project / "passport" / "material_passport.json"
    print(f"- Material Passport: {'present' if passport.exists() else 'missing'}")
    _evidence_report, evidence_issues = evidence_gate.audit_project(project)
    evidence_summary = evidence_gate.summarize(evidence_issues)
    print(
        "- Evidence gate: "
        f"{evidence_summary['status']} "
        f"(ERROR={evidence_summary['ERROR']}, WARN={evidence_summary['WARN']}, INFO={evidence_summary['INFO']})"
    )

    print("\n## Suggested Next Actions")
    for action in next_actions(project):
        print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
