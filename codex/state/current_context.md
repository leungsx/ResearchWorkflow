# Current Context

Last updated: 2026-06-29

## Durable Summary

The user is building a Codex-first scientific research workflow under `/Users/leung/ResearchWorkflow`. The workflow should cover literature search, PDF handling, literature notes, Obsidian knowledge management, experiment execution, Python/R/MATLAB integration, Gephi network visualization, scientific figures, writing, formatting, and integrity checks.

The user has clarified that they will mainly interact through Codex and does not want to manually organize files or literature. Codex is expected to archive daily work, synthesize weekly reviews, maintain context packs, track files and open loops, and adapt to the user's thinking style over time.

The user's current main research-writing context is Chinese research. The default target journal is 《图书情报工作》, so manuscript drafting, literature organization, data governance, figure/table preparation, AI disclosure, and submission checks should default to a Chinese library and information science / information resource management context unless the user names another venue.

The user's main literature source is expected to be CNKI/知网. CNKI access should use the user's own legal institutional/library/VPN/browser login. Codex must not receive CNKI passwords or bypass CAPTCHA, paywalls, download limits, or access controls; Codex can operate within a user-authorized local browser session and can import/analyze legally exported metadata and authorized full texts.

## Current Implemented State

- `ResearchWorkflow` project scaffold exists.
- Obsidian vault exists at `/Users/leung/ResearchWorkflow/vault`.
- Gephi is installed and configured at `/Applications/Gephi.app/Contents/MacOS/gephi`.
- Anaconda Python, Rscript, and Pandoc are detected.
- PDF extraction backends `pymupdf`/`fitz`, `pdfplumber`, and `pypdf` are installed in the Anaconda environment.
- `starter_project` exists as a template/example project.
- `make status PROJECT=<slug>` provides project status and suggested next actions.
- Literature search, PDF download/extraction, literature matrix import, Gephi export, experiment logging, and material passport scripts exist.
- `make codex-sweep DATE=<date>` records files modified during an active research day.
- `docs/USER_VISUAL_GUIDE.md` is the primary user-facing visual guide explaining implemented/planned features, use cases, and simple Codex prompts.
- `docs/USABLE_FUNCTIONS_TEST_GUIDE.md` is the practical function test and usage manual. It lists currently usable workflow capabilities by research scenario, including purpose, inputs, outputs, test commands, natural-language prompts, and cautions.
- `Idea Lab` has been added for brainstorming, idea cards, frontier scans, FINER filtering, and promotion from idea to research project.
- `Happy Research Loop` has been added to connect inspiration, hypotheses, experiment design, reproducibility, result interpretation, literature alignment, and paper claims.
- `Knowledge Coach` has been added to teach concepts and research methods, create Obsidian notes, maintain review queues, and export knowledge graphs.
- A `publication production layer` has been added after reviewing the installed `nature-*` skills. New project templates now include publication readiness, terminology ledger, polishing log, source-grounded reader package folder, figure-contract guidance, presentation planning, and reviewer-response tracker.
- `make status PROJECT=<slug>` now reports publication readiness, terminology ledger, reader packages, presentation decks, and reviewer-response trackers, while ignoring empty template files.
- Typora is installed at `/Applications/Typora.app` and has been integrated as the local Markdown preview/editing surface. Use `make typora FILE=<path>` or `make typora-project PROJECT=<slug> DOC=<key>` to open workflow files.
- A context-budget layer has been added. Startup should read hot state first: `current_context.md`, `open_loops.md`, `user_model.md`, and `context_index.md`. Compact daily summaries live under `vault/07_Codex_Logs/compact_daily/`; raw daily logs and file sweeps are cold audit records, not default startup context.
- A fast-lane architecture layer has been added to reduce token/time cost for small research tasks. Micro tasks such as checking the next paper recommendation or locating a Reader should use `make fast-status PROJECT=<slug> TOPIC="<topic>"` and the generated `codex/runtime/<project>_fast_snapshot.md` instead of updating dashboards, running file sweep, compacting logs, or rerunning evidence gate. Standard/deep tasks still update canonical evidence and archive at closeout. The policy is documented in `docs/WORKFLOW_ARCHITECTURE_FASTLANE.md` and `codex/OPERATING_PROTOCOL.md`.
- A Chinese target-journal layer has been added for 《图书情报工作》. The workflow now has an official-source-based journal profile, default Chinese manuscript skeleton, submission checklist, AI-usage disclosure template, data dictionary/governance templates, and Chinese literature matrix fields for CNKI/万方/维普/manual sources, CSSCI status, Chinese-reference English translations, and target-journal relevance.
- `workflow.yaml` now records `default_target_journal: 图书情报工作` and points to `docs/journal_profiles/tushuqingbaogongzuo.md`.
- Four practical finishing tools now exist for the Chinese journal workflow:
  `make backfill PROJECT=<slug> APPLY=1` adds newly introduced template files to old projects without overwriting existing drafts; `make evidence-gate PROJECT=<slug>` checks whether metadata-only, abstract-only, AI-summarized, unread, or source-locator-free materials are being used as manuscript evidence; `make citation-audit PROJECT=<slug>` writes `manuscript/citation_audit_gbt7714.md` with deterministic GB/T 7714, Chinese-reference English-translation, and evidence-gate checks; `make submission-package PROJECT=<slug>` builds a local 《图书情报工作》 submission package with manuscript, optional DOCX, reference audit, evidence-gate report, data availability statement, AI disclosure, figure/spec files, integrity materials, cover-letter draft, checksums, and manifest while intentionally excluding raw data.
- `starter_project` has been backfilled to the latest template, has one citation audit, and has test submission packages proving the package generator and Pandoc DOCX conversion work.
- CNKI intake now exists. `make import-cnki INPUT=<file-or-dir> TAG=<project_slug>` imports CNKI-exported CSV/TSV/XLSX/RIS/EndNote text into `library/literature_matrix.csv`, sets `source_database=CNKI`, marks rows as `metadata-only`, creates deterministic citekeys, skips duplicates, and writes reports under `library/cnki_exports/import_reports/`. The Anaconda environment has `pandas` and `openpyxl`; legacy `.xls` may still require `xlrd`.
- CNKI frontier learning now exists. `make cnki-frontier TAG=<project_slug> TOPIC="<topic>"` creates a 5-7 paper metadata-level frontier digest under `vault/15_CNKI_Frontier/digests/`; `make paper-brief CITEKEY=<citekey>` creates a one-paper discussion card under `vault/15_CNKI_Frontier/paper_briefs/`; `make paper-reader PROJECT=<slug> CITEKEY=<citekey> PDF=<authorized_pdf>` creates a source-grounded full-paper reader under `literature/readers/<citekey>/` without automatically marking the paper as human-read.
- CNKI daily learning recommendation now exists. `make cnki-daily PROJECT=<project_slug> TOPIC="<topic>"` creates one daily primary-paper recommendation under `vault/15_CNKI_Frontier/daily_recommendations/`, using `library/literature_matrix.csv` as the screened candidate gate and CNKI export JSON/CSV only for citation/download metrics and URLs. It maintains `projects/<project>/literature/recommendation_profile.json` for user/topic preferences and `daily_learning_state.json` to avoid repeating prior daily recommendations. The default learning progression is high-impact foundations, then review/map papers, then recent important work, then method/model papers.
- CNKI browser-assisted download has been calibrated on a real project. Chrome JavaScript from Apple Events can trigger CNKI download links inside the user's authorized browser session; when Chrome/macOS shows a save dialog, the user clicks `保存`, and Codex then checks `Downloads`, copies the authorized file into the project library, normalizes the filename, and updates `library/literature_matrix.csv`. System-level coordinate clicking via `osascript` is still blocked by macOS Accessibility, so save dialogs remain user-clicked.
- CNKI full-text download preference was refined on 2026-06-21. Future browser-assisted downloads should default to the paper-detail-page PDF route: click the paper title from the CNKI result list, open the detail/abstract page, then click `PDF下载`. Result-list direct download is now only a fallback because it often returns `.caj`. `make cnki-download PROJECT=<slug> TITLES=<titles.txt>` wraps `scripts/cnki_click_download_titles.py`, whose default `--download-mode detail-pdf-first` tries detail-page PDF first, result-list direct download second, and CAJ conversion third.
- CNKI acquisition strategy was refined again on 2026-06-21 after the user pushed back on script-heavy browser automation. Use official Codex Chrome extension / `@Chrome` as the primary, visible surface for signed-in CNKI UI operations when available; scripts should supplement it for low-token local bookkeeping, PDF validation, file normalization, matrix updates, CAJ conversion, and Reader/context-pack generation.
- CNKI CAJ conversion now exists. `make caj-convert PROJECT=<slug> SCAN=1` classifies `.caj` files as true KDH/CAJ or PDF-with-CAJ-extension. `make caj-convert PROJECT=<slug> CITEKEY=<citekey> UPDATE=1 RUN_READER=1` converts true CAJ/KDH files to local PDFs, verifies them with Poppler, writes conversion reports/previews, updates `library/literature_matrix.csv`, and builds reader packages. MuPDF `mutool` is installed at `/opt/homebrew/bin/mutool`; open-source `caj2pdf` is cloned under `tools/caj2pdf/`.
- A user-facing workflow entry layer now exists. `vault/Home.md` is the first start page for "what can I do now"; `projects/library_short_video/00_project_dashboard.md` is the current project dashboard; `projects/library_short_video/literature/reading_board.md` explains today's recommended papers, where to read them, what discussion cards/readers/insight-bank cards are for, and which natural-language prompts to use. `make home` opens the Home page, and `make reading-board PROJECT=library_short_video` opens the active project's reading board in Typora.
- Token-light guided-reading context packs now exist. `make paper-context PROJECT=<slug> CITEKEY=<citekey>` writes `projects/<slug>/literature/context_packs/<citekey>.md`; `make paper-context PROJECT=<slug> ALL=1` writes packs for all skimmed/human-read/verified project papers. The pack combines Reader Reading Notes,研讨卡核心理解, innovation-limitation excerpts, and a small evidence block snapshot so co-reading can start without reloading the full Reader. For `library_short_video`, 7 context packs exist for the 7 skimmed papers. `docs/PAPER_READING_OUTPUT_STANDARD.md` defines the roles of reading board, context pack,研讨卡, Reader, and innovation-limitation bank; `docs/PLUGIN_INSPIRED_RESEARCH_WORKFLOW_OPTIMIZATION.md` records the plugin-inspired design review.
- A literature-review workbench layer now exists. `docs/LITERATURE_REVIEW_WORKBENCH.md` turns screenshot-style prompts into a durable workflow for per-paper conclusion tables, cross-paper logical classification, literature-review logic lines, stage-level paper work summaries, and evidence-boundary warnings. `projects/_template/literature/literature_review_workbench.md` is the reusable project template. For `library_short_video`, `projects/library_short_video/literature/literature_review_workbench.md` summarizes the 7 source-grounded skimmed papers into four logical clusters: status/service baseline, content/interaction mechanisms, digital-reading/service conversion, and theory/method frameworks. `make lit-workbench PROJECT=<slug>` opens the workbench in Typora.
- A browser-first daily learning layer now exists. `paper_reading/today.html` is the fixed daily paper-reading entry; `study_dashboard.html` is the overview; `paper_reading/views/`, `knowledge_cards/views/`, and `logs/views/` contain HTML mirrors for Markdown source files so the user can click and read without seeing raw Markdown. `knowledge_graph/index.html` is an interactive SVG graph with search, filters, and node detail. `scripts/build_learning_dashboard.py` auto-generates mirrors and rewrites local Markdown links in daily paper pages.
- Workflow health and backup now exist. `make workflow-audit` writes `workflow_health.html` and `vault/07_Codex_Logs/workflow_audits/<date>-workflow-audit.md`, checking entry links, mirror freshness, graph visualization, review queue, archive, backup, and context compression. `make workflow-backup` writes lightweight critical-state zip files under `backups/` and `backups/index.html`, excluding PDFs/raw data/caches. `make workflow-refresh DATE=<date> NOTE="<note>"` is the no-race daily closeout command: graph -> dashboard -> backup -> file sweep -> compact -> context index -> audit -> final dashboard refresh.

## Latest Workflow Review

- 2026-06-29 end-to-end usability review implemented the HTML-first daily-reading standard, interactive graph view, workflow audit, lightweight backups, dashboard health panel, and no-race `make workflow-refresh` closeout. Current audit status is FAIL=0, WARN=2: due review items (`方向链`, `Hook Model 上瘾模型`) and harmless workspace hygiene items (`.DS_Store`, `__pycache__`).
- 2026-06-19 architecture review fixes implemented: evidence-state enforcement, deterministic paper-reader handoff, context compaction coverage for appended entries, `.xlsx` CNKI import, and submission-package evidence gate reporting. Remaining high-value work is calibration on a real CNKI export, authorized full text, and a real Chinese LIS / 《图书情报工作》 project.
- 2026-06-20 user ran a real CNKI learning workflow for `图书馆短视频相关研究`. Project `library_short_video` now has CNKI metadata, a frontier radar, 7 authorized CNKI originals, 7 discussion cards for the current learning set, and 7 reader packages. Status is summarized in `projects/library_short_video/literature/cnki_retrieval_status.md`. The two former true-CAJ gaps (`cnki_2020_64b4f881c9`, `cnki_2023_34348faa1e`) were converted with local `caj2pdf` to verified PDFs under `library/pdfs/library_short_video/converted/` and readers were generated. No paper should be marked `human-read` or `verified` merely because a reader exists.
- Later on 2026-06-20, Codex continued the pilot by reading `cnki_2021_d35f8e895a` at source-grounded reader level, filling reader Reading Notes, upgrading its paper brief, populating `projects/library_short_video/03_literature_synthesis.md`, refreshing `01_research_question.md`, setting its literature-matrix `read_status` to `skimmed` only, regenerating evidence gate and Material Passport. Project status now shows literature synthesis filled, Material Passport present, Evidence gate WARNINGS with ERROR=0; the paper is still not `human-read` or `verified`.
- Later on 2026-06-20, Codex optimized the recurring CNKI learning flow with `scripts/cnki_daily_recommend.py`, `make cnki-daily`, and `docs/CNKI_DAILY_LEARNING.md`. For `library_short_video`, the generated profile records the user's preference to start from high-citation/high-download field papers, move to review/map papers, then newer important research, then method/model deep dives. Today's daily recommendation file is `vault/15_CNKI_Frontier/daily_recommendations/2026-06-20-library_short_video.md`; the current primary is `cnki_2021_dfab60236e` because the highest target-journal anchor `cnki_2021_d35f8e895a` has already been skimmed but not verified.
- Later on 2026-06-20, Codex started a source-grounded co-reading session for `cnki_2021_dfab60236e`, filled its reader Reading Notes, upgraded its discussion card, expanded `projects/library_short_video/03_literature_synthesis.md`, and upgraded its literature-matrix `read_status` to `skimmed`. The main conclusion is that this paper is a useful large-sample external benchmark and method template for reading-promotion short-video transmission effects, but its sample is socialized accounts rather than library-operated accounts, so it should not be treated as direct library-scene evidence.
- Later on 2026-06-20, Codex added a durable innovation-limitation-opportunity bank for `library_short_video`: `projects/library_short_video/literature/innovation_limitation_bank.md`. It currently contains classified cards for `cnki_2021_d35f8e895a` and `cnki_2021_dfab60236e`, with cross-paper opportunities such as interaction metrics versus library service value, Hook Model plus ELM integration, official-library versus socialized-account comparison, 2024-2026 data renewal, and multimodal variable expansion. `scripts/insight_bank.py`, `make insight-bank`, `docs/CNKI_DAILY_LEARNING.md`, and `scripts/cnki_daily_recommend.py` now support adding/checking an insight card after each future main-paper reading.
- Later on 2026-06-20, Codex completed the three companion papers from the daily recommendation: `cnki_2020_64b4f881c9`, `cnki_2021_7556aafa99`, and `cnki_2020_2a150c6df8`. All three now have guided companion Reading Notes, upgraded paper briefs, literature-matrix `read_status=skimmed`, synthesis entries, and innovation-limitation bank cards. The bank now has 5 cards. Evidence gate remains ERROR=0, with WARN=4 only for the two remaining synthesis-referenced but metadata-only reader candidates (`cnki_2023_34348faa1e`, `cnki_2021_5530e86157`).
- Later on 2026-06-20, the user said the workflow still felt opaque despite many backend features: they did not know what functions existed, where to read today's papers, what discussion cards/readers were, how to visualize them, or how they helped. Codex added a user-facing start layer: `vault/Home.md` as the first entry, `projects/library_short_video/00_project_dashboard.md` as the current project dashboard, `projects/library_short_video/literature/reading_board.md` as the CNKI daily reading board, and Typora shortcuts `make home` and `make reading-board PROJECT=library_short_video`.
- Later on 2026-06-20, the user asked Codex to review local OpenAI plugins and use any useful ideas to improve token use, Reader co-reading,研讨卡 structure, and overall experience. Codex reviewed relevant plugin patterns including Notion research/knowledge capture, Zotero local citation boundaries, Scite/Hebbia evidence-backed answers, Readwise/Reader highlights, meeting-intelligence summaries/action items, and CircleCI chunk/cache patterns. Instead of enabling external account dependencies, Codex ported the patterns locally: `scripts/paper_context_pack.py`, `make paper-context`, five `library_short_video` context packs, `docs/PAPER_READING_OUTPUT_STANDARD.md`, `docs/PLUGIN_INSPIRED_RESEARCH_WORKFLOW_OPTIMIZATION.md`, and updated Home/reading board/project dashboard entries.
- Later on 2026-06-20, Codex used the 5 context packs to create a quick cross-paper recap at `projects/library_short_video/literature/recaps/2026-06-20-five-paper-quick-recap.md` and linked it from the reading board and project dashboard. The recap's main synthesis is that the literature has progressed from early status/problem diagnosis to public-library service mapping, hot-content rules, official-library Hook Model testing, and socialized-account ELM benchmarking; the main gap is still the weak connection between platform interaction metrics and actual library service/reading-promotion value.
- Later on 2026-06-20, the user asked what Hook Model means. Codex created a beginner concept note at `vault/02_Concepts/Hook Model 上瘾模型.md`, a learning-session note at `vault/12_Learning_Log/sessions/2026-06-20-hook-model.md`, and a review-queue item. Working interpretation for this project: Hook Model = trigger, action, variable reward, investment; in library short-video research it should be used to explain valuable repeated service engagement, not simple traffic chasing.
- On 2026-06-21, the user clarified an important CNKI operation detail: result-list download tends to provide CAJ, while clicking the paper title and then `PDF下载` on the detail page can provide PDF. Codex updated the CNKI script, Makefile entry, workflow docs, usability guide, and `library_short_video` retrieval status accordingly. Codex also checked the current official Codex manual: for signed-in websites, the recommended official route is the Codex Chrome extension / `@Chrome`; Computer Use can operate GUI apps and browsers when installed and permitted; the in-app `@Browser` is mainly for local/public unauthenticated pages. The durable CNKI browser strategy is hybrid: use Chrome extension as the primary signed-in browser surface when available, but keep local scripts as the primary batch/low-token surface for extraction, downloading known titles, file organization, CAJ conversion, readers, recommendations, and context packs.
- Later on 2026-06-21, Codex generated the daily recommendation for `library_short_video`. Today's primary was `cnki_2021_5530e86157` 张承 2021《基于短视频营销的公共图书馆数字阅读推广策略研究》. Codex completed a guided source-grounded skim, upgraded its `read_status` to `skimmed`, filled Reader Reading Notes, rewrote its paper brief, added it to `03_literature_synthesis.md`, added innovation/limitation/opportunity entry O-009 to `innovation_limitation_bank.md`, refreshed `reading_board.md`, generated `projects/library_short_video/literature/context_packs/cnki_2021_5530e86157.md`, and reran evidence gate. Evidence gate remains ERROR=0, WARN=2, both for remaining metadata-only `cnki_2023_34348faa1e`.
- Later on 2026-06-21, the user asked Codex to re-login/re-enter CNKI, refresh keyword search results, and use the updated detail-page PDF strategy. Codex searched CNKI `主题 = 图书馆 * 短视频`, date range `2019-01-01` to `2026-06-21`; CNKI showed 914 total results and 604 journal results. The current first page was exported to `library/cnki_exports/library_short_video/cnki_library_short_video_current.*` and dated snapshots; importing skipped all 20 rows as duplicate title/year, so the matrix stayed at 20 project-tagged rows but current metrics were refreshed. The refreshed recommendation selected `cnki_2021_3771e58987` 龚雪竹 2021《公共图书馆和高校图书馆短视频营销比较研究》.
- Later on 2026-06-21, the detail-page PDF-first route was live-tested. CNKI/browser intermediate pages can still save `.html` or empty files if the wrong browser save route is used, so future workflow must validate file type and extractable text before updating `pdf_path`. The user manually completed the real PDF download; Codex found `公共图书馆和高校图书馆短视频营销比较研究_龚雪竹.pdf` on the desktop, copied it to `library/pdfs/library_short_video/cnki_2021_3771e58987.pdf`, verified it as a 10-page PDF, generated a Reader, filled Reading Notes, upgraded the paper brief, updated `03_literature_synthesis.md`, added the paper to `innovation_limitation_bank.md`, generated `projects/library_short_video/literature/context_packs/cnki_2021_3771e58987.md`, updated dashboards, and set `read_status=skimmed`.
- Later on 2026-06-21, Codex fixed `scripts/cnki_daily_recommend.py` so daily discovery skips `skimmed`, `human-read`, `verified`, and `discarded` papers for new primary recommendations. After the fix, the next unread high-impact recommendation became `cnki_2020_5ca581e54f` 曾一昕、张齐婕 2020《公共图书馆短视频公众平台建设现状分析》. `library_short_video` now has 8 local full texts/readers, 7 source-grounded skimmed papers, 13 metadata-only rows, and evidence gate ERROR=0/WARN=2, both for `cnki_2023_34348faa1e`.
- Later on 2026-06-21, the user raised a workflow architecture concern: small tasks felt slow and token-expensive because each one triggered logging, file sweeps, dashboard updates, compact summaries, and multi-file synchronization. Codex implemented the fast-lane architecture: `scripts/research_fastlane.py`, `make fast-status`, `make workflow-policy`, `make codex-event`, and `make codex-close-{fast,standard,deep}`. The current `library_short_video` fast snapshot is `codex/runtime/library_short_video_fast_snapshot.md`; it reports the next unread candidate as `cnki_2020_5ca581e54f`.
- Later on 2026-06-21, the user asked whether custom scripts were really necessary for CNKI or whether OpenAI/Codex Chrome extension could be used. Official Codex manual guidance supports using the Chrome extension for signed-in browser state, the in-app browser for unauthenticated/local pages, and Computer Use for GUI tasks that structured tools cannot handle. The working decision for CNKI is Chrome-extension-first for search/navigation/detail-page PDF download, with scripts only for validation and local archive/database updates.
- On 2026-06-28, the user provided screenshots of a social-media paper-writing prompt about summarizing articles, classifying literature, deriving literature-review logic lines, and avoiding fabricated details. Codex converted these prompts into the ResearchWorkflow literature-review workbench layer, updated Home/project dashboard/reading board/reading-output standard, and created a filled `library_short_video` workbench. The key working rule is: use prompt ideas to structure evidence-aware intermediate artifacts, not to directly generate unverified long-form literature review prose.

## Current Priority

Implement and follow the Codex-first collaboration layer:

- daily logs
- weekly reviews
- current context pack
- user model
- open-loop tracking
- session start/closeout protocol

## Key Files

- `/Users/leung/AGENTS.md`
- `/Users/leung/ResearchWorkflow/codex/OPERATING_PROTOCOL.md`
- `/Users/leung/ResearchWorkflow/codex/state/user_model.md`
- `/Users/leung/ResearchWorkflow/codex/state/open_loops.md`
- `/Users/leung/ResearchWorkflow/codex/state/current_context.md`
- `/Users/leung/ResearchWorkflow/docs/USABILITY_REVIEW.md`
- `/Users/leung/ResearchWorkflow/vault/Home.md`
- `/Users/leung/ResearchWorkflow/docs/USER_VISUAL_GUIDE.md`
- `/Users/leung/ResearchWorkflow/docs/USABLE_FUNCTIONS_TEST_GUIDE.md`
- `/Users/leung/ResearchWorkflow/docs/PAPER_READING_OUTPUT_STANDARD.md`
- `/Users/leung/ResearchWorkflow/docs/LITERATURE_REVIEW_WORKBENCH.md`
- `/Users/leung/ResearchWorkflow/docs/PLUGIN_INSPIRED_RESEARCH_WORKFLOW_OPTIMIZATION.md`
- `/Users/leung/ResearchWorkflow/docs/WORKFLOW_ARCHITECTURE_FASTLANE.md`
- `/Users/leung/ResearchWorkflow/docs/IDEA_LAB.md`
- `/Users/leung/ResearchWorkflow/docs/HAPPY_RESEARCH_LOOP.md`
- `/Users/leung/ResearchWorkflow/docs/EXPERIMENT_TO_CLAIM.md`
- `/Users/leung/ResearchWorkflow/docs/KNOWLEDGE_COACH.md`
- `/Users/leung/ResearchWorkflow/docs/OBSIDIAN_KNOWLEDGE_GRAPH.md`
- `/Users/leung/ResearchWorkflow/docs/NATURE_SKILL_INTEGRATION.md`
- `/Users/leung/ResearchWorkflow/docs/CNKI_WORKFLOW.md`
- `/Users/leung/ResearchWorkflow/docs/CAJ_WORKFLOW.md`
- `/Users/leung/ResearchWorkflow/docs/CNKI_FRONTIER_RADAR.md`
- `/Users/leung/ResearchWorkflow/docs/CNKI_DAILY_LEARNING.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/innovation_limitation_bank.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/literature_review_workbench.md`
- `/Users/leung/ResearchWorkflow/docs/journal_profiles/tushuqingbaogongzuo.md`
- `/Users/leung/ResearchWorkflow/docs/DATA_AND_FIGURE_RULES.md`
- `/Users/leung/ResearchWorkflow/README.md`
- `/Users/leung/ResearchWorkflow/projects/_template/08_publication_readiness.md`
- `/Users/leung/ResearchWorkflow/projects/_template/manuscript/target_journal.md`
- `/Users/leung/ResearchWorkflow/projects/_template/manuscript/submission_checklist_tushuqingbaogongzuo.md`
- `/Users/leung/ResearchWorkflow/projects/_template/manuscript/ai_usage_disclosure.md`
- `/Users/leung/ResearchWorkflow/projects/_template/manuscript/terminology_ledger.md`
- `/Users/leung/ResearchWorkflow/projects/_template/manuscript/polishing_log.md`
- `/Users/leung/ResearchWorkflow/projects/_template/data/data_dictionary.md`
- `/Users/leung/ResearchWorkflow/projects/_template/data/data_governance.md`
- `/Users/leung/ResearchWorkflow/library/chinese_literature_import_template.csv`
- `/Users/leung/ResearchWorkflow/library/cnki_exports/README.md`
- `/Users/leung/ResearchWorkflow/projects/_template/figures/specs/figure_spec.md`
- `/Users/leung/ResearchWorkflow/scripts/backfill_project.py`
- `/Users/leung/ResearchWorkflow/scripts/audit_references_gbt7714.py`
- `/Users/leung/ResearchWorkflow/scripts/make_submission_package.py`
- `/Users/leung/ResearchWorkflow/scripts/evidence_gate.py`
- `/Users/leung/ResearchWorkflow/scripts/import_cnki_to_matrix.py`
- `/Users/leung/ResearchWorkflow/scripts/cnki_frontier_digest.py`
- `/Users/leung/ResearchWorkflow/scripts/cnki_daily_recommend.py`
- `/Users/leung/ResearchWorkflow/scripts/cnki_click_download_titles.py`
- `/Users/leung/ResearchWorkflow/scripts/insight_bank.py`
- `/Users/leung/ResearchWorkflow/scripts/paper_context_pack.py`
- `/Users/leung/ResearchWorkflow/scripts/paper_brief.py`
- `/Users/leung/ResearchWorkflow/scripts/paper_reader.py`
- `/Users/leung/ResearchWorkflow/scripts/caj_convert.py`
- `/Users/leung/ResearchWorkflow/scripts/research_fastlane.py`
- `/Users/leung/ResearchWorkflow/codex/runtime/library_short_video_fast_snapshot.md`
- `/Users/leung/ResearchWorkflow/vault/15_CNKI_Frontier/README.md`
- `/Users/leung/ResearchWorkflow/scripts/open_in_typora.py`
- `/Users/leung/ResearchWorkflow/scripts/codex_compact.py`
- `/Users/leung/ResearchWorkflow/config/software_paths.yaml`
- `/Users/leung/ResearchWorkflow/codex/state/context_index.md`
- `/Users/leung/ResearchWorkflow/vault/07_Codex_Logs/compact_daily/2026-06-19-summary.md`
- `/Users/leung/ResearchWorkflow/vault/07_Codex_Logs/file_sweeps/2026-06-19-file-sweep.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/cnki_search_plan.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/cnki_retrieval_status.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/00_project_dashboard.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/reading_board.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/context_packs/`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/recaps/2026-06-20-five-paper-quick-recap.md`
- `/Users/leung/ResearchWorkflow/vault/02_Concepts/Hook Model 上瘾模型.md`
- `/Users/leung/ResearchWorkflow/vault/12_Learning_Log/sessions/2026-06-20-hook-model.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/03_literature_synthesis.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/readers/cnki_2021_d35f8e895a/paper.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/readers/cnki_2020_64b4f881c9/paper.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/readers/cnki_2021_7556aafa99/paper.md`
- `/Users/leung/ResearchWorkflow/projects/library_short_video/literature/readers/cnki_2020_2a150c6df8/paper.md`
