PYTHON ?= python3
PYTHONDONTWRITEBYTECODE ?= 1
export PYTHONDONTWRITEBYTECODE
ACTIVE_PROJECT ?= $(shell PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/get_active_project.py)

.PHONY: check new status project-state review-state review-studied review-studied-due review-server review-server-start review-server-ensure review-server-stop review-server-status search-index workflow-state action-queue collaboration-state archive-policy schema-validate fast-status workflow-policy workflow-render workflow-audit-readonly workflow-audit-refresh workflow-audit workflow-test workflow-backup workflow-backup-prune workflow-refresh workflow-refresh-git git-snapshot backfill backfill-all evidence-gate evidence-locators manuscript-panel incoming-triage lit-transition citation-audit submission-package search import-matrix import-cnki cnki-frontier cnki-daily cnki-handoff cnki-intake cnki-download cnki-batch-download cnki-restock insight-bank paper-brief paper-reader paper-context caj-convert download extract gephi passport home reading-board lit-workbench typora typora-project codex-start codex-event codex-close-fast codex-close-standard codex-close-deep codex-weekly codex-sweep codex-compact codex-compact-all codex-context-index codex-context-audit idea-start idea-status compare-results knowledge-status obsidian-graph learning-dashboard

check:
	$(PYTHON) scripts/check_environment.py

new:
	$(PYTHON) scripts/new_project.py "$(SLUG)" "$(TITLE)"

status:
	$(PYTHON) scripts/project_status.py --project "$(if $(PROJECT),$(PROJECT),$(ACTIVE_PROJECT))"

project-state:
	$(PYTHON) scripts/build_project_state.py $(if $(PROJECT),--project "$(PROJECT)",--all)

review-state:
	$(PYTHON) scripts/build_review_state.py $(if $(DATE),--date "$(DATE)",)

review-studied:
	$(PYTHON) scripts/mark_review_studied.py $(if $(ID),--id "$(ID)",) $(if $(DATE),--date "$(DATE)",) $(if $(NEXT_DAYS),--next-days "$(NEXT_DAYS)",)

review-studied-due:
	$(PYTHON) scripts/mark_review_studied.py --all-due $(if $(DATE),--date "$(DATE)",) $(if $(NEXT_DAYS),--next-days "$(NEXT_DAYS)",)

review-server:
	$(PYTHON) scripts/review_mark_server.py $(if $(PORT),--port "$(PORT)",)

review-server-start:
	$(PYTHON) scripts/review_server_control.py start $(if $(PORT),--port "$(PORT)",)

review-server-ensure:
	$(PYTHON) scripts/review_server_control.py start $(if $(PORT),--port "$(PORT)",)

review-server-stop:
	$(PYTHON) scripts/review_server_control.py stop $(if $(PORT),--port "$(PORT)",)

review-server-status:
	$(PYTHON) scripts/review_server_control.py status $(if $(PORT),--port "$(PORT)",)

search-index:
	$(PYTHON) scripts/build_search_index.py

workflow-state:
	$(PYTHON) scripts/build_workflow_state.py

action-queue:
	$(PYTHON) scripts/build_action_queue.py

collaboration-state:
	$(PYTHON) scripts/build_collaboration_state.py

archive-policy:
	$(PYTHON) scripts/build_archive_policy.py

schema-validate:
	$(PYTHON) scripts/validate_workflow_schemas.py

fast-status:
	$(PYTHON) scripts/research_fastlane.py snapshot --project "$(PROJECT)" $(if $(TOPIC),--topic "$(TOPIC)",) $(if $(DATE),--date "$(DATE)",) $(if $(PRINT),--print,)

workflow-policy:
	$(PYTHON) scripts/research_fastlane.py policy

workflow-render:
	$(MAKE) workflow-state
	$(MAKE) action-queue
	$(MAKE) collaboration-state
	$(MAKE) archive-policy

workflow-audit-readonly:
	$(PYTHON) scripts/workflow_audit.py --readonly $(if $(DATE),--date "$(DATE)",) $(if $(STRICT),--strict,)

workflow-audit-refresh:
	$(MAKE) workflow-render
	$(MAKE) workflow-audit-readonly $(if $(DATE),DATE="$(DATE)",) $(if $(STRICT),STRICT=1,)

workflow-audit: workflow-audit-readonly

workflow-test:
	$(PYTHON) scripts/workflow_tests.py

workflow-backup:
	$(PYTHON) scripts/workflow_backup.py $(if $(DATE),--date "$(DATE)",) $(if $(NOTE),--note "$(NOTE)",) $(if $(KEEP),--keep "$(KEEP)",)

workflow-backup-prune:
	$(PYTHON) scripts/workflow_backup.py --prune-only --keep "$(KEEP)"

workflow-refresh:
	$(MAKE) review-server-ensure
	$(MAKE) obsidian-graph
	$(MAKE) learning-dashboard
	$(MAKE) workflow-backup $(if $(DATE),DATE="$(DATE)",) $(if $(NOTE),NOTE="$(NOTE)",)
	$(MAKE) codex-sweep $(if $(DATE),DATE="$(DATE)",)
	$(MAKE) codex-compact $(if $(DATE),DATE="$(DATE)",)
	$(MAKE) codex-context-index
	$(MAKE) workflow-audit $(if $(DATE),DATE="$(DATE)",)
	$(MAKE) learning-dashboard

workflow-refresh-git:
	$(MAKE) workflow-refresh $(if $(DATE),DATE="$(DATE)",) $(if $(NOTE),NOTE="$(NOTE)",)
	$(MAKE) git-snapshot $(if $(DATE),DATE="$(DATE)",) $(if $(NOTE),NOTE="$(NOTE) pre-audit snapshot",) PUSH=1
	$(MAKE) workflow-audit $(if $(DATE),DATE="$(DATE)",)
	$(MAKE) learning-dashboard
	$(MAKE) git-snapshot $(if $(DATE),DATE="$(DATE)",) $(if $(NOTE),NOTE="$(NOTE) audit refresh",) PUSH=1

git-snapshot:
	$(PYTHON) scripts/git_snapshot.py --init $(if $(DATE),--date "$(DATE)",) $(if $(NOTE),--note "$(NOTE)",) $(if $(PUSH),--push,) $(if $(DRY),--dry-run,) $(if $(ALLOW_RISKY),--allow-risky,)

backfill:
	$(PYTHON) scripts/backfill_project.py --project "$(PROJECT)" $(if $(APPLY),--apply,)

backfill-all:
	$(PYTHON) scripts/backfill_project.py --all $(if $(APPLY),--apply,)

evidence-gate:
	$(PYTHON) scripts/evidence_gate.py --project "$(if $(PROJECT),$(PROJECT),$(ACTIVE_PROJECT))" $(if $(STRICT),--fail-on-errors,)

evidence-locators:
	$(PYTHON) scripts/build_evidence_locators.py --project "$(if $(PROJECT),$(PROJECT),$(ACTIVE_PROJECT))"

manuscript-panel:
	$(PYTHON) scripts/build_manuscript_panel.py --project "$(if $(PROJECT),$(PROJECT),$(ACTIVE_PROJECT))"

incoming-triage:
	$(PYTHON) scripts/scan_incoming_pdfs.py --project "$(if $(PROJECT),$(PROJECT),$(ACTIVE_PROJECT))" $(if $(INCOMING),--incoming-dir "$(INCOMING)",)

lit-transition:
	$(PYTHON) scripts/transition_literature_state.py --citekey "$(CITEKEY)" --to "$(TO)" $(if $(FROM),--from-status "$(FROM)",) $(if $(REASON),--reason "$(REASON)",) $(if $(EVIDENCE),--evidence "$(EVIDENCE)",) $(if $(PROJECT),--project "$(PROJECT)",) $(if $(DRY),--dry-run,)

citation-audit:
	$(PYTHON) scripts/audit_references_gbt7714.py --project "$(PROJECT)" $(if $(STRICT),--fail-on-errors,)

submission-package:
	$(PYTHON) scripts/make_submission_package.py --project "$(PROJECT)" $(if $(NO_DOCX),--no-docx,) $(if $(STRICT),--strict,)

search:
	$(PYTHON) scripts/literature_search.py "$(Q)" --limit 30

import-matrix:
	$(PYTHON) scripts/import_search_to_matrix.py --csv "$(CSV)"

import-cnki:
	$(PYTHON) scripts/import_cnki_to_matrix.py --input $(INPUT) $(if $(TAG),--tag "$(TAG)",) $(if $(DRY),--dry-run,)

cnki-frontier:
	$(PYTHON) scripts/cnki_frontier_digest.py $(if $(TAG),--tag "$(TAG)",) $(if $(TOPIC),--topic "$(TOPIC)",) $(if $(KEYWORDS),--keywords "$(KEYWORDS)",) $(if $(LIMIT),--limit "$(LIMIT)",) $(if $(SINCE),--since-year "$(SINCE)",)

cnki-daily:
	$(PYTHON) scripts/cnki_daily_recommend.py --project "$(PROJECT)" $(if $(TOPIC),--topic "$(TOPIC)",) $(if $(DATE),--date "$(DATE)",) $(if $(STAGE),--stage "$(STAGE)",) $(if $(COMPANIONS),--companions "$(COMPANIONS)",) $(if $(OUTPUT),--output "$(OUTPUT)",) $(if $(PROFILE),--profile "$(PROFILE)",) $(if $(NO_STATE),--no-update-state,)

cnki-handoff:
	$(PYTHON) scripts/cnki_human_download_handoff.py request $(if $(PROJECT),--project "$(PROJECT)",) $(if $(TOPIC),--topic "$(TOPIC)",) $(if $(DATE),--date "$(DATE)",) $(if $(STAGE),--stage "$(STAGE)",) $(if $(COUNT),--count "$(COUNT)",) $(if $(PROFILE),--profile "$(PROFILE)",) $(if $(OPEN),--open-cnki,) $(if $(ALLOW_EXTERNAL),--allow-external,)

cnki-intake:
	$(PYTHON) scripts/cnki_human_download_handoff.py intake $(if $(PROJECT),--project "$(PROJECT)",) $(if $(REQUEST),--request "$(REQUEST)",) $(if $(INCOMING),--incoming-dir "$(INCOMING)",) $(if $(TARGET),--target-dir "$(TARGET)",) $(if $(BUILD_READERS),--build-readers,) $(if $(MOVE),--move,)

cnki-download:
	$(PYTHON) scripts/cnki_click_download_titles.py $(if $(TITLE),--title "$(TITLE)",) $(if $(TITLES),--titles-file "$(TITLES)",) $(if $(PROJECT),--target-dir "library/pdfs/$(PROJECT)",) $(if $(MODE),--download-mode "$(MODE)",) $(if $(TIMEOUT),--timeout "$(TIMEOUT)",) $(if $(DETAIL_TIMEOUT),--detail-timeout "$(DETAIL_TIMEOUT)",) $(if $(DELAY_MIN),--delay-min "$(DELAY_MIN)",) $(if $(DELAY_MAX),--delay-max "$(DELAY_MAX)",) $(if $(CONFIRM_SAVE),--confirm-save-dialog,) $(if $(SAVE_DIALOG_DELAY),--save-dialog-delay "$(SAVE_DIALOG_DELAY)",) $(if $(NO_STOP_ON_BARRIER),--no-stop-on-barrier,) --update-matrix

cnki-batch-download:
	$(PYTHON) scripts/cnki_batch_pdf_download.py $(if $(METADATA),--metadata-json "$(METADATA)",) $(if $(PROJECT),--project "$(PROJECT)" --target-dir "library/pdfs/$(PROJECT)",) $(if $(TARGET_TOTAL),--target-total "$(TARGET_TOTAL)",) $(if $(LIMIT),--limit "$(LIMIT)",) $(if $(TIMEOUT),--timeout "$(TIMEOUT)",) $(if $(NAV_TIMEOUT),--nav-timeout "$(NAV_TIMEOUT)",) $(if $(DELAY_MIN),--delay-min "$(DELAY_MIN)",) $(if $(DELAY_MAX),--delay-max "$(DELAY_MAX)",) $(if $(CONFIRM_SAVE),--confirm-save-dialog,) $(if $(SAVE_DIALOG_DELAY),--save-dialog-delay "$(SAVE_DIALOG_DELAY)",) $(if $(PROFILE_FILTER),--profile-filter,) $(if $(NO_STOP_ON_BARRIER),--no-stop-on-barrier,) --update-matrix

cnki-restock:
	$(PYTHON) scripts/cnki_restock_learning_papers.py $(if $(PROJECT),--project "$(PROJECT)",) $(if $(TOPIC),--topic "$(TOPIC)",) $(if $(DATE),--date "$(DATE)",) $(if $(STAGE),--stage "$(STAGE)",) $(if $(MIN_STORED),--min-stored "$(MIN_STORED)",) $(if $(REFILL_COUNT),--refill-count "$(REFILL_COUNT)",) $(if $(PROFILE),--profile "$(PROFILE)",) $(if $(TIMEOUT),--timeout "$(TIMEOUT)",) $(if $(NAV_TIMEOUT),--nav-timeout "$(NAV_TIMEOUT)",) $(if $(DELAY_MIN),--delay-min "$(DELAY_MIN)",) $(if $(DELAY_MAX),--delay-max "$(DELAY_MAX)",) $(if $(CONFIRM_SAVE),--confirm-save-dialog,) $(if $(SAVE_DIALOG_DELAY),--save-dialog-delay "$(SAVE_DIALOG_DELAY)",) $(if $(NO_STOP_ON_BARRIER),--no-stop-on-barrier,) $(if $(ALLOW_NON_PDF),--allow-non-pdf-fallback,) $(if $(DRY),--dry-run,)

insight-bank:
	$(PYTHON) scripts/insight_bank.py --project "$(PROJECT)" $(if $(CITEKEY),--citekey "$(CITEKEY)",) $(if $(DRY),--dry-run,)

paper-brief:
	$(PYTHON) scripts/paper_brief.py $(if $(CITEKEY),--citekey "$(CITEKEY)",) $(if $(TITLE),--title "$(TITLE)",) $(if $(PDF),--pdf "$(PDF)",)

paper-reader:
	$(PYTHON) scripts/paper_reader.py $(if $(PROJECT),--project "$(PROJECT)",) $(if $(CITEKEY),--citekey "$(CITEKEY)",) $(if $(TITLE),--title "$(TITLE)",) $(if $(PDF),--pdf "$(PDF)",) $(if $(TEXT),--text "$(TEXT)",) $(if $(OUTPUT),--output-dir "$(OUTPUT)",) $(if $(UPDATE),--update-matrix,)

paper-context:
	$(PYTHON) scripts/paper_context_pack.py --project "$(PROJECT)" $(if $(CITEKEY),--citekey "$(CITEKEY)",) $(if $(ALL),--all-skimmed,) $(if $(OUTPUT),--output "$(OUTPUT)",) $(if $(MAX_BLOCKS),--max-blocks "$(MAX_BLOCKS)",) $(if $(SNIPPET_CHARS),--snippet-chars "$(SNIPPET_CHARS)",)

caj-convert:
	$(PYTHON) scripts/caj_convert.py --project "$(PROJECT)" $(if $(CITEKEY),--citekey "$(CITEKEY)",) $(if $(INPUT),--input "$(INPUT)",) $(if $(OUTPUT),--output "$(OUTPUT)",) $(if $(CONVERTER),--converter "$(CONVERTER)",) $(if $(SCAN),--scan,) $(if $(ALL),--all,) $(if $(OVERWRITE),--overwrite,) $(if $(UPDATE),--update-matrix,) $(if $(RUN_READER),--run-reader,)

download:
	$(PYTHON) scripts/download_oa_pdfs.py

extract:
	$(PYTHON) scripts/extract_pdf_text.py

gephi:
	$(PYTHON) scripts/export_gephi.py

passport:
	$(PYTHON) scripts/make_passport.py --project "$(PROJECT)"

home:
	$(PYTHON) scripts/open_in_typora.py

reading-board:
	$(PYTHON) scripts/open_in_typora.py --project "$(PROJECT)" --doc reading

lit-workbench:
	$(PYTHON) scripts/open_in_typora.py --project "$(PROJECT)" --doc litworkbench

typora:
	$(PYTHON) scripts/open_in_typora.py "$(FILE)"

typora-project:
	$(PYTHON) scripts/open_in_typora.py --project "$(PROJECT)" --doc "$(DOC)"

codex-start:
	$(MAKE) review-server-ensure
	$(PYTHON) scripts/codex_archive.py start $(if $(DATE),--date "$(DATE)",)

codex-event:
	$(PYTHON) scripts/research_fastlane.py event $(if $(PROJECT),--project "$(PROJECT)",) $(if $(KIND),--kind "$(KIND)",) $(if $(SUMMARY),--summary "$(SUMMARY)",) $(if $(FILE),--file "$(FILE)",) $(if $(DECISION),--decision "$(DECISION)",) $(if $(OPEN_LOOP),--open-loop "$(OPEN_LOOP)",) $(if $(NEXT_ACTION),--next-action "$(NEXT_ACTION)",) $(if $(DATE),--date "$(DATE)",)

codex-close-fast:
	$(PYTHON) scripts/research_fastlane.py close --mode fast $(if $(PROJECT),--project "$(PROJECT)",) $(if $(TOPIC),--topic "$(TOPIC)",) --summary "$(SUMMARY)" $(if $(FILE),--file "$(FILE)",) $(if $(DECISION),--decision "$(DECISION)",) $(if $(OPEN_LOOP),--open-loop "$(OPEN_LOOP)",) $(if $(NEXT_ACTION),--next-action "$(NEXT_ACTION)",) --snapshot

codex-close-standard:
	$(PYTHON) scripts/research_fastlane.py close --mode standard $(if $(PROJECT),--project "$(PROJECT)",) $(if $(TOPIC),--topic "$(TOPIC)",) --summary "$(SUMMARY)" $(if $(FILE),--file "$(FILE)",) $(if $(DECISION),--decision "$(DECISION)",) $(if $(OPEN_LOOP),--open-loop "$(OPEN_LOOP)",) $(if $(NEXT_ACTION),--next-action "$(NEXT_ACTION)",) --snapshot

codex-close-deep:
	$(PYTHON) scripts/research_fastlane.py close --mode deep $(if $(PROJECT),--project "$(PROJECT)",) $(if $(TOPIC),--topic "$(TOPIC)",) --summary "$(SUMMARY)" $(if $(FILE),--file "$(FILE)",) $(if $(DECISION),--decision "$(DECISION)",) $(if $(OPEN_LOOP),--open-loop "$(OPEN_LOOP)",) $(if $(NEXT_ACTION),--next-action "$(NEXT_ACTION)",) --snapshot

codex-weekly:
	$(PYTHON) scripts/codex_archive.py weekly $(if $(DATE),--date "$(DATE)",)

codex-sweep:
	$(PYTHON) scripts/codex_file_sweep.py $(if $(DATE),--date "$(DATE)",)

codex-compact:
	$(PYTHON) scripts/codex_compact.py compact $(if $(DATE),--date "$(DATE)",)

codex-compact-all:
	$(PYTHON) scripts/codex_compact.py compact-all $(if $(BEFORE),--before "$(BEFORE)",)

codex-context-index:
	$(PYTHON) scripts/codex_compact.py index

codex-context-audit:
	$(PYTHON) scripts/codex_compact.py audit

idea-start:
	$(PYTHON) scripts/idea_lab.py start --topic "$(TOPIC)" $(if $(MODE),--mode "$(MODE)",)

idea-status:
	$(PYTHON) scripts/idea_lab.py status

compare-results:
	$(PYTHON) scripts/compare_results.py --expected "$(EXPECTED)" --actual "$(ACTUAL)" --output "$(OUTPUT)"

knowledge-status:
	$(PYTHON) scripts/knowledge_coach.py status

obsidian-graph:
	$(PYTHON) scripts/obsidian_graph_export.py

learning-dashboard:
	$(PYTHON) scripts/scan_incoming_pdfs.py --project "$(ACTIVE_PROJECT)"
	$(PYTHON) scripts/build_evidence_locators.py --project "$(ACTIVE_PROJECT)"
	$(PYTHON) scripts/build_manuscript_panel.py --project "$(ACTIVE_PROJECT)"
	$(PYTHON) scripts/build_project_state.py --all
	$(PYTHON) scripts/build_workflow_state.py
	$(PYTHON) scripts/build_action_queue.py
	$(PYTHON) scripts/build_collaboration_state.py
	$(PYTHON) scripts/build_archive_policy.py
	$(PYTHON) scripts/build_learning_dashboard.py
	$(PYTHON) scripts/build_project_state.py --all
	$(PYTHON) scripts/build_workflow_state.py
	$(PYTHON) scripts/build_action_queue.py
	$(PYTHON) scripts/build_collaboration_state.py
	$(PYTHON) scripts/build_archive_policy.py
