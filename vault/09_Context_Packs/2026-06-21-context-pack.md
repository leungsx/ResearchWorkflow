# Context Pack - 2026-06-21

## Current Research State

The active workspace is `/Users/leung/ResearchWorkflow`. The user is optimizing a Codex-first research workflow, currently focused on CNKI literature retrieval and guided reading for the `library_short_video` pilot project.

On 2026-06-21 the user clarified that CNKI search-result-page download tends to return CAJ only, while clicking a paper title and then using `PDF下载` on the detail/abstract page can obtain a PDF. This became the new default download policy.

Later on 2026-06-21 the user raised a higher-level architecture problem: the workflow was too slow for small tasks because every recommendation/status action could trigger logs, sweeps, compact summaries, dashboards, and multi-file synchronization. Codex implemented a fast-lane architecture so micro tasks use a runtime snapshot and quick ledger first, while standard/deep tasks keep the stronger evidence and archival boundaries.

## Active Projects

- `library_short_video`: CNKI-based Chinese LIS learning workflow for 图书馆短视频相关研究.

## Key Files

- `scripts/cnki_click_download_titles.py`
- `Makefile`
- `docs/CNKI_WORKFLOW.md`
- `docs/WORKFLOW_ARCHITECTURE_FASTLANE.md`
- `docs/USER_VISUAL_GUIDE.md`
- `docs/USABLE_FUNCTIONS_TEST_GUIDE.md`
- `scripts/research_fastlane.py`
- `codex/runtime/library_short_video_fast_snapshot.md`
- `projects/library_short_video/literature/cnki_retrieval_status.md`
- `codex/state/current_context.md`
- `codex/state/open_loops.md`
- `codex/state/user_model.md`

## Key Decisions

- Future CNKI full-text downloads should use detail-page PDF first: result list title -> detail/abstract page -> `PDF下载`.
- Result-list direct download is a fallback because it often returns `.caj`.
- If only CAJ/KDH is obtained legally, use `make caj-convert PROJECT=<slug> CITEKEY=<citekey> UPDATE=1 RUN_READER=1`.
- The new user-facing command is `make cnki-download PROJECT=<slug> TITLES=<titles.txt>`.
- Browser/tool strategy: use Codex Chrome extension / `@Chrome` as the preferred signed-in CNKI browser surface when available; keep local scripts as the default batch/low-token surface; reserve Computer Use for GUI-only fallback steps.
- Strategy correction after user feedback: CNKI acquisition should not be script-only. Use official Codex Chrome extension / `@Chrome` as the primary, user-visible way to operate signed-in CNKI pages when available; scripts should supplement it by validating downloaded files, renaming/copying PDFs, updating `literature_matrix.csv`, generating Readers/context packs, and keeping batch state.
- For small workflow tasks, use fast-lane mode: `make fast-status PROJECT=<slug> TOPIC="<topic>"` and `codex/runtime/<project>_fast_snapshot.md`. Do not rerun sweep, compact, evidence gate, dashboard rewrites, or context-pack regeneration for recommendation-only/status-only/path lookup tasks.
- Standard tasks include PDF validation, Reader generation, guided reading completion, `read_status` changes, synthesis changes, and innovation-limitation-bank changes. Deep tasks include architecture changes, manuscript/citation/submission work, milestone synthesis, and weekly review.

## Literature State

- Daily recommendation generated for 2026-06-21: primary paper `cnki_2021_5530e86157` 张承 2021《基于短视频营销的公共图书馆数字阅读推广策略研究》.
- Codex completed a guided source-grounded skim of `cnki_2021_5530e86157`. It is now `skimmed`, not `human-read` or `verified`.
- Later the user asked Codex to re-enter CNKI, refresh the keyword search, and use the detail-page PDF download strategy. CNKI search `主题 = 图书馆 * 短视频`, date range `2019-01-01` to `2026-06-21`, returned 914 total results and 604 journal results. The current first page was exported to `library/cnki_exports/library_short_video/cnki_library_short_video_current.*` and dated snapshots; importing skipped all 20 rows as duplicate title/year.
- The refreshed recommendation selected `cnki_2021_3771e58987` 龚雪竹 2021《公共图书馆和高校图书馆短视频营销比较研究》. User manually completed the real PDF download after an HTML intermediate-save issue. Codex copied the PDF to `library/pdfs/library_short_video/cnki_2021_3771e58987.pdf`, verified it as a 10-page PDF, generated a Reader, and completed a source-grounded guided skim.
- `cnki_2021_3771e58987` is now `skimmed`, with Reader notes, paper brief, innovation/limitation bank entry, literature synthesis entry, reading-board link, and context pack at `projects/library_short_video/literature/context_packs/cnki_2021_3771e58987.md`.
- `library_short_video` now has 8 local full texts/readers, 7 source-grounded skimmed papers, and 13 metadata-only rows. Evidence gate after the update: ERROR=0, WARN=2, both for `cnki_2023_34348faa1e`.
- The daily recommender was adjusted so `skimmed`, `human-read`, `verified`, and `discarded` are skipped for new primary recommendations. The next unread high-impact recommendation is `cnki_2020_5ca581e54f`《公共图书馆短视频公众平台建设现状分析》.
- The current fast runtime snapshot is `codex/runtime/library_short_video_fast_snapshot.md`. It reports 20 CNKI matrix rows, 8 local full texts/readers, 7 context packs, read statuses `skimmed`=7 and `metadata-only`=13, evidence gate ERROR=0/WARN=2, and next unread candidate `cnki_2020_5ca581e54f`.

## Experiment / Data State

- `scripts/cnki_click_download_titles.py` now defaults to `--download-mode detail-pdf-first`, tries detail-page PDF with short polling, falls back to result-list direct download, detects recent downloaded PDF/CAJ/NH files, copies them to the project PDF library, and updates `library/literature_matrix.csv`.
- Verified with `python3 -m py_compile`, `python3 scripts/cnki_click_download_titles.py --help`, and `make -n cnki-download ...`.
- The detail-page PDF route has been live validated once, but CNKI/browser intermediate pages can still save `.html` or empty files if the wrong save path is used. Future downloads must validate file type and extractable text before updating the matrix.
- `make cnki-daily PROJECT=library_short_video TOPIC="图书馆短视频相关研究"` produced `/Users/leung/ResearchWorkflow/vault/15_CNKI_Frontier/daily_recommendations/2026-06-21-library_short_video.md`.
- `make paper-context PROJECT=library_short_video CITEKEY=cnki_2021_5530e86157` produced `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/context_packs/cnki_2021_5530e86157.md`.
- `make fast-status PROJECT=library_short_video TOPIC="图书馆短视频相关研究"` produced `/Users/leung/ResearchWorkflow/codex/runtime/library_short_video_fast_snapshot.md`.
- `make workflow-policy` prints the micro/standard/deep routing policy.

## Writing / Figure State

No manuscript, figure, or analysis-data changes in this turn.

## Open Loops

- Test the new CNKI detail-page PDF-first route on live CNKI pages.
- Decide whether the user wants to set up official Codex Chrome extension / Computer Use for smoother browser control.
- If the user installs/enables the official Chrome extension, validate one complete CNKI daily acquisition cycle with `@Chrome` plus local scripts, then update the routine based on actual friction and token cost.
- For the 60-PDF goal, switch to a Chrome-extension-first routine: `@Chrome` handles CNKI search/result navigation/detail-page PDF download, while local scripts monitor/import/validate the files and update the matrix.
- Read the remaining current-learning-set paper `cnki_2023_34348faa1e` and update synthesis/bank/context pack.
- Download/read the next unread high-impact paper `cnki_2020_5ca581e54f`.
- Use fast-lane by default for future "next paper/status/path" queries; use standard/deep closeout only when the task changes evidence state, user-facing navigation, or project milestones.

## User Preferences

- The user wants Codex to turn workflow discoveries into durable defaults.
- For CNKI, the user prefers detail-page PDF downloads over result-list CAJ downloads where authorized PDF is available.
- The user wants fast responses and lower token use for small workflow actions. Avoid over-maintaining logs and dashboards during micro tasks.
- The user prefers a visible Chrome-extension-first browser workflow over opaque custom scripts for CNKI page operations, while still accepting scripts for low-token local bookkeeping and validation.

## Next Recommended Actions

- For the next CNKI batch, prepare a title list and run `make cnki-download PROJECT=library_short_video TITLES=<titles.txt>`, then validate that the saved file is a real PDF/CAJ rather than HTML.
- If downloaded files are still CAJ, run `make caj-convert PROJECT=library_short_video CITEKEY=<citekey> UPDATE=1 RUN_READER=1`.
- For the next recommendation-only turn, start from `make fast-status PROJECT=library_short_video TOPIC="图书馆短视频相关研究" PRINT=1` rather than regenerating all dashboards and archives.
