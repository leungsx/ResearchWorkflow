# User Model

Last updated: 2026-06-29

## Explicit Preferences

- The user wants Codex to be the primary interface for research work.
- The user does not want to manually organize files, literature, daily notes, or weekly summaries.
- The user expects Codex to proactively classify, archive, summarize, and improve the workflow.
- The user prefers Chinese for workflow discussion.
- The user's main research context is Chinese research, with 《图书情报工作》 as the current default target journal.
- The user's main literature source is likely CNKI/知网; they prefer Codex to operate the CNKI page when they provide local browser access, while keeping access legal and not sharing passwords.
- For CNKI full-text downloads, the user prefers the detail-page PDF route: click the paper title from search results, enter the paper detail page, then click `PDF下载`; result-list download is only a fallback because it often returns CAJ.
- The user does not want CNKI browser acquisition to become a script-only black box. Prefer official Codex Chrome extension / `@Chrome` as the visible primary surface for signed-in CNKI page operation when available, with local scripts only as a supplement for metadata capture, file validation, renaming, matrix updates, and repeatable batch bookkeeping.
- The user is interested in reducing token usage in the daily paper-acquisition and learning workflow. Prefer local scripts, local Markdown, readers, context packs, and saved matrices for repeatable work; use browser/GUI control only for signed-in access and unstable UI steps.
- The user explicitly feels the workflow becomes slow when small tasks trigger full logging, file sweeps, compact summaries, and dashboard synchronization. For small tasks, prefer the fast-lane architecture: quick runtime snapshot/ledger first, standard/deep archival only when evidence state, user-facing navigation, or project milestones change.
- The user wants an ongoing CNKI-based learning routine: regularly identify 5-7 frontier papers, discuss the set, then pick one paper for deeper reading and methodological/innovation analysis.
- The user wants daily paper recommendations and joint reading/discussion. Recommendation order should start with the most cited/high-value field papers, then review/status/map papers, then gradually move into newer important studies, with guidance from shallow to deep.
- For every recommended main-reading paper, the user wants innovations, limitations, and reusable improvement/research opportunities classified and accumulated so later ideas can be mined from them.
- The user wants visible, user-facing entry points for the workflow. Backend automation is not enough: Codex should show what functions exist, where artifacts live, how to open/read today's papers, what discussion cards/readers/insight-bank cards mean, and how these artifacts help future research.
- The user explicitly wants daily paper reading to be HTML-first and click-to-read: one fixed entry, clean visual pages, no default raw Markdown jumps, and a knowledge graph that looks and behaves like a graph rather than a table.
- The user values workflow health, backup, archive, and traceability as first-class features. After user-facing or evidence-state changes, prefer `make workflow-refresh DATE=<date>` so dashboard, graph, backups, file sweep, compact context, and audit stay synchronized.
- The user wants Codex to actively learn from useful plugin/workflow designs and port them into the research workflow when they improve token efficiency, Reader-guided co-reading, discussion-card quality, or usability.
- The user also wants useful external prompt patterns, including screenshot/social-media prompt examples, to be converted into durable local workflow templates rather than kept as one-off chat prompts.
- The user wants an end-to-end scientific workflow covering literature, experiments, writing, figures, Obsidian knowledge management, and software orchestration.
- The user commonly uses Typora to read Markdown and is comfortable having Codex open workflow Markdown files there when needed.

## Working Style Signals

- The user thinks in systems and workflows rather than isolated tasks.
- The user asks for critique and improvement, not just implementation.
- The user values convenience, continuity, and low manual overhead.
- The user expects the assistant to manage context over long-running work.
- The user explicitly wants work to be recoverable after terminal closure; durable local logs, context packs, open loops, and project status files should be kept up to date during long workflows.

## Assistance Strategy

- Start from current context and active project status.
- Convert broad goals into concrete local artifacts.
- Keep user-facing replies concise, while maintaining detailed local records.
- Proactively identify workflow gaps and implement small structural fixes.
- When a task creates durable research state, update logs and context files before final response. For micro tasks, use fast-lane snapshot/quick ledger and avoid unnecessary multi-file updates.

## Confidence Notes

- The preferences above are explicit or strongly repeated in the conversation.
- Do not infer the user's research field until they provide a concrete project topic.
