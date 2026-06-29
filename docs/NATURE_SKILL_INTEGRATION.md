# Nature Skill Integration Notes

This document records which parts of the installed `nature-*` skills are worth
absorbing into `ResearchWorkflow`. The goal is not to replace ARS. ARS remains
the research-to-paper backbone; the nature skills add production-grade artifacts
for reading, terminology, polishing, figures, slides, and reviewer response.

## Useful Patterns To Borrow

| Source skill | Useful pattern | Workflow artifact |
|---|---|---|
| `nature-reader` | Full-paper source map with stable block IDs, bilingual reading notes, uncertainty notes, extracted figures near first substantive mention | `literature/readers/<paper_key>/paper.md`, `source_map.json`, `translation_notes.md`, `assets/` |
| `nature-polishing` | Diagnose structure before sentence polish; route by paper type, section, source language, and target journal; maintain a terminology ledger | `manuscript/terminology_ledger.md`, `manuscript/polishing_log.md` |
| `nature-figure` | Figure contract before plotting: one-sentence claim, evidence chain, archetype, backend gate, export/QA contract | `figures/specs/<figure_id>.md` |
| `nature-paper2ppt` | Argument-first deck workflow, selected figure assets, asset manifest, self-review, text-overflow QA | `presentations/<talk_slug>/`, `qa_report.md`, `asset_manifest.md` |
| `nature-response` | Comment-response tracker with editor/reviewer IDs, severity, proposed action, missing author input, readiness state | `review_response/response_tracker.md` |

## Recommended Routing

Use ARS for the research logic:

- research question narrowing
- literature synthesis
- manuscript structure
- integrity verification
- peer-review simulation
- revision planning

Use the nature-derived production layer when the user asks for:

- "读这篇论文 / 精读 / 中英文对照": create a reader package with source anchors.
- "润色 / 改写 / Nature style": update terminology ledger first, then log polishing decisions.
- "画图 / 论文图 / Nature style figure": write a figure contract before code.
- "论文做 PPT / 组会汇报": build a presentation package with asset manifest and QA report.
- "审稿回复 / rebuttal / response letter": build a comment-response tracker before prose.

## Production Layer Artifacts

Each project may contain these optional but high-value artifacts:

- `08_publication_readiness.md`: score the project across RQ, literature, data, experiments, figures, manuscript, integrity, and communication readiness.
- `manuscript/terminology_ledger.md`: canonical terms, first-use definitions, variants, and decisions.
- `manuscript/polishing_log.md`: what was polished, which section logic changed, and what still needs author input.
- `figures/specs/*.md`: one contract per final figure, not just a caption.
- `literature/readers/`: full-paper reading packages with source maps.
- `presentations/`: paper-to-PPT packages and QA reports.
- `review_response/`: reviewer comment tracker and response package.

## Quality Gates

- Do not sentence-polish a structurally wrong section; first diagnose the section job.
- Do not draw a publication figure before the figure's claim and evidence chain are explicit.
- Do not let final figures exist without specs that name data, script, statistics, export format, and integrity notes.
- Do not build slides from decorative figures; every selected figure must serve the argument.
- Do not draft reviewer responses that invent experiments, line numbers, figure panels, citations, or manuscript changes.
- Do not treat AI summaries as verified reading. Reader packages must mark extraction confidence and uncertainty.

## Minimal Project Workflow

1. Build or update `01_research_question.md`.
2. Read key papers into `literature/readers/` when full-paper grounding matters.
3. Write claims in `07_claim_evidence_map.md`.
4. Before drafting or polishing, update `manuscript/terminology_ledger.md`.
5. Before final figure generation, create `figures/specs/<figure_id>.md`.
6. Before submission or a formal report, update `08_publication_readiness.md`.
7. For talks, build `presentations/<talk_slug>/` with assets and `qa_report.md`.
8. For revisions, build `review_response/response_tracker.md` before response prose.
