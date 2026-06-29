# ResearchWorkflow Fast-Lane Architecture

Last updated: 2026-06-21

## Why This Exists

The workflow had become too heavy for daily use: a small action such as updating
the next CNKI recommendation could trigger daily-log edits, file sweeps, compact
summaries, project dashboard edits, reading-board edits, evidence-gate checks,
and context-pack updates.

That is accurate, but not ergonomic. The new architecture separates quick
interaction from archival maintenance.

## Architecture Layers

| Layer | Role | Files | Update Frequency |
|---|---|---|---|
| Runtime snapshot | Fast current status for Codex and user | `codex/runtime/<project>_fast_snapshot.md` | micro tasks, on demand |
| Quick ledger | Lightweight event trace | `codex/runtime/quick_events.jsonl` | micro tasks |
| Canonical data | Source of truth | `library/literature_matrix.csv`, PDFs, Readers, context packs, synthesis files | when evidence changes |
| User-facing views | Human navigation | `vault/Home.md`, project dashboard, reading board | when the user's next action changes |
| Audit archive | Durable history and recovery | daily logs, file sweeps, compact summaries, context packs | standard/deep closeout |
| Integrity gates | Evidence safety | evidence gate, citation audit, passport | manuscript/evidence milestones |

## Operating Modes

### Micro

Use for:

- "今天下一篇推荐是什么？"
- "打开当前阅读入口。"
- "快速复盘这篇论文。"
- "这篇 paper 的 reader 在哪里？"
- "现在项目还差什么？"

Behavior:

- read hot state and runtime snapshot
- update `codex/runtime/quick_events.jsonl` if a trace is useful
- refresh `codex/runtime/<project>_fast_snapshot.md`
- avoid full sweep, compact, evidence gate, dashboard rewrites

Command:

```bash
make fast-status PROJECT=library_short_video TOPIC="图书馆短视频相关研究"
make codex-event PROJECT=library_short_video SUMMARY="Checked next unread CNKI candidate."
make codex-close-fast PROJECT=library_short_video SUMMARY="Closed a micro recommendation/status turn."
```

### Standard

Use for:

- a PDF/CAJ was validated and linked
- a Reader was generated
- a paper was guided-read and marked `skimmed`
- synthesis or innovation-limitation bank changed
- the reading board needs to show a new next action

Behavior:

- update the affected canonical files
- update only the visible board that changed
- append one daily closeout entry
- run evidence gate only if evidence status/source locators changed
- run file sweep at closeout

Command:

```bash
make codex-close-standard PROJECT=library_short_video SUMMARY="Completed guided skim and updated canonical reading artifacts."
```

### Deep

Use for:

- architecture changes
- research-question narrowing
- milestone synthesis
- manuscript/citation/submission work
- weekly review

Behavior:

- update docs, hot state, open loops, and user-facing entry points
- run relevant integrity checks
- run sweep and compact

Command:

```bash
make codex-close-deep PROJECT=library_short_video SUMMARY="Updated workflow architecture and context policy."
```

## Daily CNKI Reading Rule

The daily CNKI loop now runs as:

1. Fast recommendation from matrix and cached CNKI metrics.
2. Download only the chosen full text when needed.
3. Validate file type and extractable text before updating `pdf_path`.
4. Generate Reader/context pack only after a real full text exists.
5. Update synthesis and innovation-limitation bank after guided reading.
6. Batch archive the day at standard/deep closeout.

This keeps the repeated "what should I read next?" step fast, while preserving
source-grounded evidence when a paper actually becomes part of the project.

## Practical Defaults

- Recommendation-only: micro.
- Download/Reader creation: standard.
- Guided reading completion: standard.
- Writing claims from evidence: deep or standard with evidence gate.
- Weekly/monthly synthesis: deep.
- Architecture or protocol changes: deep.

## What This Saves

- Fewer files modified per small turn.
- Less repeated context loading.
- Less manual dashboard rewriting.
- Lower token use because Codex starts from generated snapshots/context packs.
- Better separation between "interactive learning" and "audit-grade research
  record."
