# Context Pack - 2026-06-19

## Current Research State

The user is building a Codex-first scientific research workflow under
`/Users/leung/ResearchWorkflow`. On 2026-06-19, the newly installed
`nature-*` skills were reviewed for workflow value. ARS remains the backbone
for research-to-paper logic; the useful nature-skill ideas were integrated as a
project-level publication production layer.

Typora is now integrated as the local Markdown reading/editing surface. Codex
should keep managing files and logs, and open Markdown in Typora on request.

PDF extraction backends `pymupdf`/`fitz` and `pypdf` were installed on
2026-06-19; `pdfplumber` was already available. `make check` now reports all
checked Python packages importable.

Context compaction is now implemented. Future sessions should avoid reading old
raw logs by default and should start from hot state plus `context_index.md`.
Compact daily summaries are under `vault/07_Codex_Logs/compact_daily/`.

The user's current main research-writing context is Chinese research. The
default target journal is 《图书情报工作》. New manuscript, literature, data,
figure/table, AI disclosure, and submission-readiness work should default to a
Chinese library and information science / information resource management
context unless the user names another journal.

## Active Projects

- `starter_project`: existing example project. It has been backfilled to the latest template, has a generated GB/T 7714 citation audit, and has test submission packages. Its content remains stub/example material, not a real manuscript.
- `_template`: project template now includes the new production-layer files,
  plus a Chinese-first 《图书情报工作》 manuscript skeleton, target-journal profile
  pointer, submission checklist, AI disclosure file, and data governance files.

## Key Files

- `docs/NATURE_SKILL_INTEGRATION.md`
- `docs/DATA_AND_FIGURE_RULES.md`
- `docs/journal_profiles/tushuqingbaogongzuo.md`
- `projects/_template/08_publication_readiness.md`
- `projects/_template/manuscript/paper.md`
- `projects/_template/manuscript/target_journal.md`
- `projects/_template/manuscript/submission_checklist_tushuqingbaogongzuo.md`
- `projects/_template/manuscript/ai_usage_disclosure.md`
- `projects/_template/manuscript/terminology_ledger.md`
- `projects/_template/manuscript/polishing_log.md`
- `projects/_template/data/data_dictionary.md`
- `projects/_template/data/data_governance.md`
- `library/chinese_literature_import_template.csv`
- `projects/_template/figures/specs/figure_spec.md`
- `projects/_template/literature/readers/README.md`
- `projects/_template/presentations/paper2ppt_plan.md`
- `projects/_template/review_response/response_tracker.md`
- `scripts/project_status.py`
- `scripts/backfill_project.py`
- `scripts/audit_references_gbt7714.py`
- `scripts/make_submission_package.py`
- `scripts/evidence_gate.py`
- `scripts/paper_reader.py`
- `scripts/open_in_typora.py`
- `scripts/codex_compact.py`
- `config/software_paths.yaml`
- `codex/state/context_index.md`
- `vault/07_Codex_Logs/compact_daily/2026-06-19-summary.md`

## Key Decisions

- Do not replace ARS with nature skills.
- Borrow nature skills as deliverable-specific quality gates:
  terminology ledger, polishing log, figure contract, source-grounded reader,
  PPT asset/QA package, and reviewer-response tracker.
- Figure generation should start from a claim/evidence/export contract before code.
- Manuscript polishing should start from terminology and structural diagnosis before sentence-level rewriting.
- Typora is the preferred local Markdown preview/editing tool for generated workflow files.
- Raw daily logs should be preserved but treated as cold audit records. Compact summaries and context index are the default route for reducing token use.
- Treat 《图书情报工作》 as the current default target journal unless another venue is named.
- Chinese literature is first-class evidence: record source database, language,
  publication type, CSSCI status, Chinese-reference English translation, and
  target-journal relevance when importing or curating references.
- For 《图书情报工作》, manuscripts need Chinese structured abstracts, long English
  abstracts, Chinese/English figure and table titles, GB/T 7714-2015
  references, data availability statements, and disclosed AI use when relevant.
- Old projects can be upgraded with `make backfill PROJECT=<slug> APPLY=1`,
  which copies missing template files without overwriting existing drafts.
- Finalization commands now exist: `make citation-audit PROJECT=<slug>` for
  heuristic GB/T 7714 and Chinese-reference English-translation checks, and
  `make submission-package PROJECT=<slug>` for local submission packaging.

## Literature State

- No external literature search in this turn.
- Nature skill source files were inspected locally under `~/.codex/skills/`.
- Official 《图书情报工作》 pages were checked for scope, 2026 topic guidance,
  writing template, data sharing policy, AI policy, authorship rules, and
  submission routes.

## Experiment / Data State

- No research experiment was run.
- Verification commands run: `python3 -m py_compile scripts/project_status.py`, `python3 scripts/project_status.py --project _template`, `make status PROJECT=starter_project`.
- Typora integration verification: `python3 scripts/open_in_typora.py README.md --dry-run`, `python3 scripts/open_in_typora.py --project starter_project --doc dashboard --dry-run`, and `make check`.
- Context compaction verification: `python3 -m py_compile scripts/codex_compact.py scripts/codex_archive.py`, `make codex-compact-all`, `make codex-context-audit`, and `make codex-start`.
- Chinese journal workflow verification included script compilation, project
  status checks on `_template` and `starter_project`, old-project backfill,
  citation audit generation, submission-package generation, and Pandoc DOCX
  conversion for `starter_project`.

## Writing / Figure State

- Writing workflow now has `manuscript/terminology_ledger.md` and `manuscript/polishing_log.md`.
- Writing workflow now has a Chinese-first `manuscript/paper.md` skeleton for
  《图书情报工作》, including Chinese structured abstract fields and long English
  abstract fields.
- Writing/finalization workflow now has `manuscript/citation_audit_gbt7714.md`
  as a generated audit report and `submission_package/<id>/` as the generated
  local submission package directory.
- Figure workflow now has an upgraded figure contract template and stronger `docs/DATA_AND_FIGURE_RULES.md` guidance.
- PPT and reviewer-response workflows now have project-level landing files.

## Open Loops

- Improve the 《图书情报工作》 layer beyond the MVP: current backfill, heuristic
  citation audit, submission package, and Pandoc DOCX generation work; remaining
  gap is more precise DOCX/LaTeX style templates and CSL/GB/T validation beyond
  deterministic heuristics.
- Test the Chinese literature import template on a real CNKI/万方/维普/manual
  bibliography.
- Automate readiness scoring from project files later; current readiness is manual.
- Add monthly or milestone-level synthesis if daily compact summaries become numerous.
- 2026-06-19 architecture review fixes were implemented: `make evidence-gate`,
  `make paper-reader`, compact summaries now include recent appended entries,
  CNKI `.xlsx` import works when `openpyxl` is available, and submission packages
  include evidence-gate reporting with strict-mode failure support.
- Remaining risk is no longer missing mechanics but calibration on real materials:
  a real CNKI export, authorized full texts, and a real Chinese LIS /
  《图书情报工作》 project.

## User Preferences

- User wants practical workflow improvements from installed skills, not duplication or over-routing.
- User prefers Chinese for workflow discussion.
- User's main research-writing context is Chinese, with 《图书情报工作》 as the
  current default target journal.
- User commonly reads Markdown in Typora.

## Next Recommended Actions

- When a real project is active, run `make status PROJECT=<slug>`, then fill the
  next missing production artifact only when it supports the current task.
- Next engineering improvements should prioritize a real pilot manuscript
  through the 《图书情报工作》 checklist, citation audit, and submission package;
  then refine DOCX/LaTeX style fidelity based on concrete formatting failures.
