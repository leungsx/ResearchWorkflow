#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"

PROJECT_DOCS = {
    "dashboard": "00_project_dashboard.md",
    "rq": "01_research_question.md",
    "methodology": "02_methodology.md",
    "literature": "03_literature_synthesis.md",
    "litworkbench": "literature/literature_review_workbench.md",
    "reading": "literature/reading_board.md",
    "contextpacks": "literature/context_packs",
    "cnki": "literature/cnki_retrieval_status.md",
    "insights": "literature/innovation_limitation_bank.md",
    "experiment": "04_experiment_plan.md",
    "hypotheses": "05_hypothesis_registry.md",
    "results": "06_result_interpretation.md",
    "claims": "07_claim_evidence_map.md",
    "readiness": "08_publication_readiness.md",
    "evidence": "manuscript/evidence_gate_report.md",
    "paper": "manuscript/paper.md",
    "references": "manuscript/references.bib",
    "terms": "manuscript/terminology_ledger.md",
    "polishing": "manuscript/polishing_log.md",
    "response": "review_response/response_tracker.md",
}


def resolve_target(raw_path: str | None, project: str | None, doc: str | None) -> Path:
    if project:
        doc_key = doc or "dashboard"
        if doc_key not in PROJECT_DOCS:
            choices = ", ".join(sorted(PROJECT_DOCS))
            raise ValueError(f"Unknown DOC={doc_key!r}. Available docs: {choices}")
        return PROJECTS / project / PROJECT_DOCS[doc_key]

    if not raw_path:
        return ROOT / "vault" / "Home.md"

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a Markdown workflow file in Typora.")
    parser.add_argument("path", nargs="?", help="Markdown file or folder path, relative to ResearchWorkflow if not absolute.")
    parser.add_argument("--project", help="Project slug under projects/.")
    parser.add_argument("--doc", help="Common project doc key, for example paper, terms, claims, readiness, response.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved target without opening Typora.")
    args = parser.parse_args()

    target = resolve_target(args.path, args.project, args.doc)
    if not target.exists():
        raise FileNotFoundError(f"Typora target not found: {target}")

    if args.dry_run:
        print(target)
        return 0

    subprocess.run(["open", "-a", "Typora", str(target)], check=True)
    print(f"Opened in Typora: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
