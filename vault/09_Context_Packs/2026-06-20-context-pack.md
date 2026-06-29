# Context Pack - 2026-06-20

## Current Research State

The active pilot is a CNKI-based Chinese LIS learning workflow for `图书馆短视频相关研究`, under `/Users/leung/ResearchWorkflow/projects/library_short_video`.

CNKI was accessed only through the user's authorized Chrome/VPN/institution session. Codex operated the browser for search and download triggering; the user clicked `保存` when Chrome/macOS showed a save dialog.

## Active Projects

- `library_short_video`: CNKI pilot project for library short-video studies, aligned with the user's Chinese research context and default target journal 《图书情报工作》.

## Key Files

- `projects/library_short_video/literature/cnki_search_plan.md`
- `projects/library_short_video/literature/cnki_retrieval_status.md`
- `vault/Home.md`
- `projects/library_short_video/00_project_dashboard.md`
- `projects/library_short_video/literature/reading_board.md`
- `projects/library_short_video/literature/context_packs/`
- `projects/library_short_video/literature/recaps/2026-06-20-five-paper-quick-recap.md`
- `docs/PAPER_READING_OUTPUT_STANDARD.md`
- `docs/PLUGIN_INSPIRED_RESEARCH_WORKFLOW_OPTIMIZATION.md`
- `vault/02_Concepts/Hook Model 上瘾模型.md`
- `vault/12_Learning_Log/sessions/2026-06-20-hook-model.md`
- `library/cnki_exports/library_short_video/cnki_library_short_video_current.csv`
- `library/cnki_exports/library_short_video/cnki_library_short_video_current.json`
- `library/pdfs/library_short_video/`
- `library/literature_matrix.csv`
- `vault/15_CNKI_Frontier/digests/2026-06-20-cnki-frontier.md`
- `vault/15_CNKI_Frontier/daily_recommendations/2026-06-20-library_short_video.md`
- `vault/15_CNKI_Frontier/paper_briefs/`
- `projects/library_short_video/literature/recommendation_profile.json`
- `projects/library_short_video/literature/daily_learning_state.json`
- `projects/library_short_video/literature/innovation_limitation_bank.md`
- `scripts/cnki_daily_recommend.py`
- `scripts/insight_bank.py`
- `docs/CNKI_DAILY_LEARNING.md`

## Key Decisions

- Do not bypass CNKI CAPTCHA, security checks, paywalls, or access controls.
- Browser workflow: Codex triggers CNKI links inside the authorized page; user handles login/CAPTCHA/password/save-dialog clicks.
- Do not mark CNKI papers as `human-read` or `verified` merely because files/readers exist.
- Current learning set is the actually downloaded and organized 7-paper set, which differs slightly from the initial algorithmic frontier-radar selection.
- Daily learning recommendation should use `library/literature_matrix.csv` as the candidate gate and CNKI export JSON/CSV only for metrics/URLs. This prevents broad raw CNKI noise from becoming a primary daily recommendation.
- The user's recommendation preference is: high-impact/high-citation field foundations first, then review/status/map papers, then newer important research, then method/model papers.
- Each future main-paper reading should also update the innovation-limitation-opportunity bank, so paper-level innovations and limitations can accumulate into later research ideas instead of remaining isolated reading notes.
- The workflow needs a visible user-facing entry layer, not only backend scripts and generated files. `vault/Home.md` is the start page, `projects/library_short_video/00_project_dashboard.md` is the active project dashboard, and `projects/library_short_video/literature/reading_board.md` is the current paper-reading board. Future functional additions should update a visible entry, guide, or board.
- Co-reading should now default to token-light context packs when available. `make paper-context PROJECT=library_short_video ALL=1` generated packs for the 5 skimmed papers under `projects/library_short_video/literature/context_packs/`. These packs are for efficient guided reading and cross-paper comparison, not final source evidence.

## Literature State

CNKI query used: `主题：图书馆 * 短视频`, date range `2019-01-01` to `2026-06-20`. Result page showed 914 total results and 604 journal articles.

Current learning set completion:

- Authorized originals: 7 / 7 under `library/pdfs/library_short_video/`.
- Discussion cards: 7 / 7 for the current learning set.
- Reader packages: 7 / 7.
- Reader gaps: none for the current learning set.
- CAJ conversion route: `make caj-convert PROJECT=library_short_video CITEKEY=<citekey> UPDATE=1 RUN_READER=1` is installed and verified. It uses MuPDF `mutool` plus `tools/caj2pdf/caj2pdf`, writes converted PDFs under `library/pdfs/library_short_video/converted/`, writes reports under `projects/library_short_video/literature/caj_conversion/`, and builds reader packages.

Reader packages currently exist for:

- `cnki_2021_d35f8e895a` (HTML text route; converted PDF also exists; reader notes preserved)
- `cnki_2021_dfab60236e` (CAJ converted to PDF; reader rebuilt from PDF; 23 blocks)
- `cnki_2020_64b4f881c9` (CAJ converted to PDF; 11 blocks)
- `cnki_2020_2a150c6df8` (PDF-text `.caj`, 17 blocks)
- `cnki_2021_7556aafa99` (PDF-text `.caj`, 20 blocks)
- `cnki_2023_34348faa1e` (CAJ converted to PDF; 19 blocks)
- `cnki_2021_5530e86157` (PDF-text `.caj`, 15 blocks)

Reading/synthesis update:

- `cnki_2021_d35f8e895a` has been processed through a Codex-assisted source-grounded reading session. Its reader Reading Notes now summarize method, innovation/value, usable block IDs, and limitations.
- `vault/15_CNKI_Frontier/paper_briefs/cnki_2021_d35f8e895a.md` has been upgraded from metadata-level to full-reader-level discussion status.
- `projects/library_short_video/03_literature_synthesis.md` is now filled with first-paper clusters, theory map, method map, gaps, and evidence table.
- `library/literature_matrix.csv` marks `cnki_2021_d35f8e895a` as `skimmed`, not `human-read` or `verified`.
- `make cnki-daily PROJECT=library_short_video TOPIC="图书馆短视频相关研究"` now generates a daily recommendation report. For 2026-06-20, the report is `vault/15_CNKI_Frontier/daily_recommendations/2026-06-20-library_short_video.md`, stage `foundation_high_impact`, primary paper `cnki_2021_dfab60236e` (`抖音阅读推广短视频传播效果影响因素研究`). The target-journal anchor `cnki_2021_d35f8e895a` remains in the pool but is downgraded because it is already `skimmed`.
- `cnki_2021_dfab60236e` has now also been processed through a Codex-assisted source-grounded reading session. Its reader Reading Notes and discussion card were upgraded, `03_literature_synthesis.md` now includes ELM/socialized-account evidence from this paper, and `library/literature_matrix.csv` marks it as `skimmed`.
- The main interpretive decision for `cnki_2021_dfab60236e` is to treat it as an external benchmark and method template rather than direct library-scene evidence, because its sample is 30 socialized reading-promotion Douyin accounts with more than 1 million followers rather than library-operated accounts.
- `projects/library_short_video/literature/innovation_limitation_bank.md` now contains classified cards for `cnki_2021_d35f8e895a` and `cnki_2021_dfab60236e`, plus a cross-paper opportunity map. The current strongest opportunity themes are platform interaction versus library service value, Hook Model plus ELM integration, official-library versus socialized-account comparison, 2024-2026 data renewal, multimodal variable expansion, and moving from operation advice to service-improvement validation.
- The three companion papers from the 2026-06-20 daily recommendation have also been processed through guided source-grounded skim: `cnki_2020_64b4f881c9` (2019-era status/problem/countermeasure baseline), `cnki_2021_7556aafa99` (63-public-library Douyin service map), and `cnki_2020_2a150c6df8` (popular library-video content-rule study). Their reader notes, paper briefs, `03_literature_synthesis.md`, `library/literature_matrix.csv`, daily recommendation report, and innovation-limitation bank entries were updated. The bank now has 5 cards.
- Token-light paper context packs now exist for the 5 skimmed papers: `cnki_2021_d35f8e895a`, `cnki_2021_dfab60236e`, `cnki_2020_64b4f881c9`, `cnki_2021_7556aafa99`, and `cnki_2020_2a150c6df8`. Use these first when resuming discussion, then open the full Reader only for source verification or deeper reading.
- A 5-paper quick recap now exists at `projects/library_short_video/literature/recaps/2026-06-20-five-paper-quick-recap.md`. It frames the strongest current research opportunity as moving from platform popularity metrics toward service-value and reading-promotion outcome evaluation.
- A Hook Model beginner concept note now exists. In this project, use Hook Model to explain the loop from short-video trigger to user action, variable reward, and investment; do not equate the model with simple addiction or high platform traffic.

## Experiment / Data State

No empirical dataset has been created for `library_short_video`. Current work is literature retrieval and reading infrastructure.

## Writing / Figure State

No manuscript, figures, or submission package have been developed for this project yet. `make status PROJECT=library_short_video` now reports `01_research_question.md` and `03_literature_synthesis.md` as filled; most writing, methods, experiment, target-journal, figure, and submission templates remain stubs. Material Passport is present. Evidence gate has WARNINGS but ERROR=0.

## Open Loops

- Keep the visible workflow entry layer current after future CNKI recommendation, reading, and synthesis sessions; consider an auto-refresh script or Obsidian Dataview views once several active projects exist.
- Auto-generate or refresh paper context packs after future reader generation and reading-note updates.
- Use the 5-paper quick recap to narrow 2-3 formal research questions before collecting new data.
- Cross-read the remaining reader packages `cnki_2023_34348faa1e` and `cnki_2021_5530e86157`, then refine `03_literature_synthesis.md` from reading notes into a more coherent argument map.
- Update `innovation_limitation_bank.md` after each future main-paper reading; use `make insight-bank PROJECT=library_short_video CITEKEY=<citekey>` when a card skeleton is needed.
- Use and tune `make cnki-daily` across several active-day sessions; adjust `projects/library_short_video/literature/recommendation_profile.json` if the user wants stricter target-journal weighting, broader review coverage, or faster movement to recent studies.
- Decide whether `library_short_video` remains a literature-learning/map project or narrows into an empirical article about library short-video service communication and interaction mechanisms.

## User Preferences

- User wants Codex as the primary interface and does not want to manually organize literature/files.
- User is willing to handle CNKI login, VPN, CAPTCHA, and save-dialog clicks, but expects Codex to perform search, download triggering, organization, and artifact generation.
- User wants work to be durable and recoverable if Terminal closes.
- User wants daily paper recommendations and joint learning/discussion, guided from classic/high-value field papers to reviews and then recent important research.
- User explicitly wants the innovations and limitations of each main recommended paper to be classified and accumulated for future research-idea mining.
- User explicitly said the workflow felt opaque because they could not see what functions existed, where to read papers, what discussion cards/readers were, how to visualize them, or how those cards helped. Future work should make outputs visible and operable by default.
- User asked Codex to learn from OpenAI/plugin-style workflows and use that to improve token efficiency, Reader co-reading, discussion-card format, and overall user experience.

## Next Recommended Actions

1. Run `make cnki-daily PROJECT=library_short_video TOPIC="图书馆短视频相关研究"` at the start of the next active learning session.
2. Compare `cnki_2021_dfab60236e` (socialized-account ELM benchmark) with `cnki_2021_d35f8e895a` (library-account Hook Model paper) to refine the project question around interaction metrics versus library service value.
3. Use the 5 skimmed papers to compare three candidate directions: service-value metrics, short-video service maturity, and traffic-versus-library-mission evaluation.
4. After the next source-grounded reading, update the insight bank card before closing the session.
5. For future CNKI downloads, run `make caj-convert PROJECT=<slug> SCAN=1` after organization; true CAJ/KDH files can then be converted with `make caj-convert PROJECT=<slug> CITEKEY=<citekey> UPDATE=1 RUN_READER=1`.
