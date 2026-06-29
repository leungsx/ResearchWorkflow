# Codex-First Research Operating Protocol

This protocol exists because the user will use Codex as the primary interface for research. The user does not want to manually organize files, literature, daily notes, or weekly summaries. Codex should perform those operations whenever research work happens in this workspace.

## Core Contract

1. Codex is responsible for organizing research artifacts created through the conversation.
2. Codex should not rely on the user to manually move files, classify literature, or maintain daily/weekly logs.
3. Codex must manage context growth by writing durable summaries into local files.
4. Codex must keep a user model, but update it cautiously from repeated evidence rather than single-message overfitting.
5. Codex cannot autonomously run when no Codex session exists. "Daily" and "weekly" mean: when a Codex session is active on that day/week, Codex must update the corresponding records.

## Session Start Routine

When a research session starts, or when the user asks to continue research:

```bash
cd /Users/leung/ResearchWorkflow
make codex-start
```

Then read, as needed:

- `codex/state/current_context.md`
- `codex/state/open_loops.md`
- `codex/state/user_model.md`
- `codex/state/context_index.md` when present
- today's compact summary under `vault/07_Codex_Logs/compact_daily/` when present
- today's raw log under `vault/07_Codex_Logs/daily/` only when exact chronology or details are needed
- current weekly review under `vault/08_Weekly_Reviews/`

Do not dump these files to the user. Use them to orient the work.

## During-Session Capture

Capture these items while working:

- user's explicit goals
- decisions made
- files created or modified
- literature searched, read, or discussed
- experiments or commands run
- figures/data generated
- unresolved questions
- changes in the user's preferences, constraints, or thinking style

If a session is long, compress intermediate reasoning into the daily log and keep the final answer focused.

## Session Closeout Routine

Before finishing any substantive research-workflow turn:

1. Append a concise entry to today's daily log.
2. Run `make codex-sweep` when files were created or modified.
3. Update `codex/state/current_context.md` if durable context changed.
4. Update `codex/state/open_loops.md` if new gaps or next actions appear.
5. Update `codex/state/user_model.md` only when a repeated or explicit preference is observed.
6. If the turn crosses a weekly review boundary or the user asks for review, update the weekly review file.

The closeout can be skipped only for trivial Q&A that produces no durable research state.

## Fast-Lane Policy

The workflow uses three operating levels. Choose the lightest level that preserves
research integrity.

### Micro Tasks

Examples:

- recommend the next paper from an existing matrix
- check current project status
- locate a reader, context pack, or PDF
- answer a quick workflow question
- produce a short recap from an existing context pack

Default handling:

1. Use existing hot state and generated runtime snapshots first.
2. If the task creates a durable trace, record one quick event with
   `make codex-event PROJECT=<slug> SUMMARY="..."`.
3. Refresh the generated snapshot with
   `make fast-status PROJECT=<slug> TOPIC="<topic>"` when helpful.
4. Do not run file sweep, compact, evidence gate, dashboard rewrites, or context
   pack regeneration unless the micro task changes evidence state.

### Standard Tasks

Examples:

- validate and organize a new PDF/CAJ conversion
- generate a Reader or paper context pack
- finish guided reading of a paper
- update `read_status`, synthesis, or the innovation-limitation bank
- change a user-facing board because the user's next action changed

Default handling:

1. Update the canonical artifact directly affected by the work.
2. Update user-facing boards only when the user needs the changed entry point.
3. Append one daily closeout entry, preferably through
   `make codex-close-standard PROJECT=<slug> SUMMARY="..."`.
4. Run evidence gate only when manuscript evidence, read status, or source
   locator safety changed.
5. Run sweep at closeout; compact only if the daily log grew materially.

### Deep Tasks

Examples:

- milestone synthesis
- weekly review
- research-question narrowing
- manuscript claims, citation audits, submission package, or passport
- broad architecture changes

Default handling:

1. Update hot state, open loops, and user-facing docs as needed.
2. Run the relevant integrity checks.
3. Use `make codex-close-deep PROJECT=<slug> SUMMARY="..."` or the explicit
   closeout routine.
4. Run sweep and compact before ending.

The fast-lane policy does not weaken evidence boundaries. It only prevents
low-risk micro tasks from triggering full archival and dashboard maintenance.

## Weekly Review Routine

Once per active research week, Codex should synthesize:

- main questions discussed
- decisions and rationale
- literature and methods touched
- files created or changed
- open loops
- next week's recommended priorities
- observed user thinking patterns
- workflow improvements to implement

Use:

```bash
make codex-weekly
```

Then add human-quality synthesis manually where the script leaves placeholders.

## Context Management

Use local context packs instead of relying on long chat history:

- `codex/state/current_context.md`: compressed durable state.
- `codex/state/context_index.md`: startup routing index for compact summaries, context packs, weekly reviews, and cold raw logs.
- `vault/09_Context_Packs/`: dated context snapshots.
- `vault/07_Codex_Logs/daily/`: chronological raw session record; keep for audit, not default startup reading.
- `vault/07_Codex_Logs/compact_daily/`: compact daily summaries for fast startup reading.
- `vault/08_Weekly_Reviews/`: weekly synthesis.

When context gets long, write a new context pack with:

- current research goals
- active projects
- important files
- decisions
- open questions
- user preferences
- next actions

Future sessions should resume from the context pack rather than re-reading all prior logs.

## Log Compaction Policy

The workflow uses a hot / warm / cold context model:

- Hot: `current_context.md`, `open_loops.md`, `user_model.md`, and `context_index.md`.
- Warm: compact daily summaries, current weekly review, and the latest context pack.
- Cold: raw daily logs and file sweeps.

Default startup should read hot context first and warm summaries only as needed.
Do not read old raw daily logs by default. Raw logs are preserved for audit,
exact chronology, or disputed details.

Use:

```bash
make codex-compact DATE=YYYY-MM-DD
make codex-compact-all
make codex-context-audit
```

After substantive turns, run `make codex-compact` when the daily log has grown,
when the turn creates durable context, or before ending a long session. Promote
only cross-day durable facts into `current_context.md`; leave transient
chronology in compact summaries or raw logs.

## Literature Handling

When literature is searched or discussed:

1. Save search metadata under `library/search_results/`.
2. Import relevant results into `library/literature_matrix.csv`.
3. Create or update Obsidian notes for important papers.
4. Mark whether evidence is abstract-only, AI-summarized, skimmed, human-read, or verified.
5. Do not treat AI-generated summaries as verified evidence.

## Idea Lab Handling

When the user wants brainstorming, new research ideas, topic discovery, or research direction guidance:

1. Route to deep-research Socratic mode principles: guide first, do not prematurely assign a topic.
2. Create or update an Idea Lab session under `vault/11_Idea_Lab/sessions/`.
3. Use accumulated context from `current_context.md`, `user_model.md`, `open_loops.md`, `literature_matrix.csv`, and relevant Obsidian notes.
4. Save promising ideas as idea cards under `vault/11_Idea_Lab/idea_cards/`.
5. Mark whether each idea needs a frontier scan.
6. When current frontier claims are needed, perform up-to-date literature/web lookup and record sources in `vault/11_Idea_Lab/frontier_scans/`.
7. Use FINER as an initial filter before promoting an idea to a formal research project.
8. Only create a formal project after the user has converged on at least one candidate research question.

## Happy Research Loop Handling

When the user asks for a simple, enjoyable research flow, or asks to connect ideas, experiments, results, and paper contribution:

1. Identify the current loop stage: inspiration, idea, research question, hypothesis, experiment design, run, result interpretation, claim-evidence mapping, writing, or archive.
2. Ask only the minimum necessary question to move one small step forward.
3. If a guess or expectation appears, save it in `05_hypothesis_registry.md`.
4. If data or an experiment appears, design or update `04_experiment_plan.md`.
5. If results appear, update `06_result_interpretation.md`.
6. If a paper claim appears, update `07_claim_evidence_map.md`.
7. Treat non-supportive or inconclusive results as useful information, not failure.
8. Before writing strong claims, check reproducibility, statistical interpretation, alternative explanations, and literature alignment.

## Knowledge Coach Handling

When the user asks about a concept, theory, scientific method, statistical method, research design, paper-writing concept, or anything they do not understand:

1. Teach in plain language first, with one simple example and one research example.
2. Explain common misunderstandings and how to remember the idea.
3. Connect the knowledge point to the user's current projects, Idea Lab, literature matrix, or methods notes when possible.
4. Create or update an Obsidian concept note under `vault/02_Concepts/` or method note under `vault/03_Methods/`.
5. Create a learning session under `vault/12_Learning_Log/sessions/` when the explanation is substantive.
6. Add the item to `vault/14_Review_Queue/review_queue.csv` for later review.
7. Use Obsidian `[[links]]` to connect concepts, methods, literature, projects, and ideas.
8. When useful, export the knowledge graph with `make obsidian-graph` so Gephi can visualize the user's learning and research directions.
9. Do not overcomplicate the first explanation; teach progressively and check understanding through short recall questions.

## User Model Rules

Maintain `codex/state/user_model.md`.

Record:

- stable preferences
- repeated question styles
- common friction points
- preferred output language and granularity
- research domains and methods
- collaboration expectations

Avoid:

- psychological overreach
- inferring stable traits from one message
- hiding uncertainty
- using the user model to flatter rather than improve work

## Non-Negotiable Boundaries

- Do not upload private manuscripts, raw data, or participant data to external services without explicit consent.
- Do not invent citations, paper details, software results, or file contents.
- Do not skip integrity checks for paper claims, data, or figures.
- Do not assume scheduled background work happened unless a local record proves it.
