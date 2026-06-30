# CNKI Daily Learning Recommendation

This workflow turns a CNKI project corpus into one daily paper recommendation
for Codex-guided reading and discussion.

It is different from `cnki-frontier`:

- `cnki-frontier` finds a small radar set, usually favoring recent/frontier
  items.
- `cnki-daily` builds a learning path: high-impact foundations first, then
  review/map papers, then recent important studies, then method/model papers.

## Command

```bash
make cnki-daily PROJECT=<project_slug> TOPIC="研究主题"
```

For a fast "what should I read next?" check without refreshing dashboards or
running archival maintenance, use:

```bash
make fast-status PROJECT=<project_slug> TOPIC="研究主题" PRINT=1
```

Useful options:

```bash
make cnki-daily PROJECT=<project_slug> DATE=2026-06-20
make cnki-daily PROJECT=<project_slug> STAGE=review_and_map
make cnki-daily PROJECT=<project_slug> STAGE=recent_important COMPANIONS=5
make cnki-daily PROJECT=<project_slug> NO_STATE=1
make insight-bank PROJECT=<project_slug> CITEKEY=<citekey>
make paper-context PROJECT=<project_slug> CITEKEY=<citekey>
make paper-context PROJECT=<project_slug> ALL=1
```

When the project needs more local full texts before daily reading, generate a
human download handoff instead of trying to make Codex download everything:

```bash
make cnki-handoff PROJECT=<project_slug> TOPIC="研究主题" COUNT=12
```

The user downloads the listed papers into the generated
`library/pdfs/<project_slug>/incoming/<date>/` folder, then Codex ingests them:

```bash
make cnki-intake PROJECT=<project_slug>
make cnki-daily PROJECT=<project_slug> TOPIC="研究主题"
```

Allowed stages:

- `foundation_high_impact`: high-citation, high-download, high-fit field papers.
- `review_and_map`: review, status, problem, strategy, path, and comparison papers.
- `recent_important`: newer papers that may change the problem frame.
- `method_model`: model, empirical, variable, data, and analysis-method papers.

If `STAGE` is omitted, the script advances automatically by recommendation
history: first foundations, then maps/reviews, then recent work, then methods.

## Inputs

The recommender combines:

- `library/literature_matrix.csv`: project-tagged CNKI candidates.
- `library/cnki_exports/<project_slug>/*.json|*.csv`: CNKI citation/download
  metrics and URLs, when available.
- `projects/<project_slug>/literature/recommendation_profile.json`: topic terms,
  required term groups, excluded generic topics, source preferences, and stage
  lengths.
- `projects/<project_slug>/literature/daily_learning_state.json`: previous daily
  recommendations, used to avoid repeating the same paper every day.

The recommender does not use raw CNKI export rows as the primary candidate pool.
The project literature matrix remains the gate, so broad search noise does not
automatically become a daily recommendation.

## Outputs

Daily reports are written to:

```text
vault/15_CNKI_Frontier/daily_recommendations/YYYY-MM-DD-<project_slug>.md
```

Each report contains:

- one primary paper
- companion papers
- CNKI citation/download metrics
- reader/PDF availability
- why the paper is recommended today
- a reading route
- discussion questions
- next commands and evidence-state reminders
- an insight-bank reminder for innovation, limitation, and opportunity capture

For already read papers, token-light guided-reading context packs are written to:

```text
projects/<project_slug>/literature/context_packs/<citekey>.md
```

Use these packs first when resuming discussion. Open the full Reader only when
checking source text, adding page numbers, or doing deeper reading.

## Preference File

For `library_short_video`, the profile records the current preference:

1. Start from high-citation and high-download field papers.
2. Prefer target-journal or strong LIS/information-resource-management sources.
3. Require direct fit with library short videos, reading promotion, public or
   university libraries, platform operation, or knowledge communication.
4. Exclude generic short-video papers unless used deliberately as external
   comparison.
5. Move from foundations to review/map papers, then newer work, then methods.

Edit the profile rather than the script when the user's topic preference changes.

## Daily Routine

1. For a quick check, run `make fast-status PROJECT=<project_slug> TOPIC="主题" PRINT=1`.
2. If the recommended candidates do not have local full text, run `make cnki-handoff PROJECT=<project_slug> TOPIC="主题" COUNT=12` and ask the user to download into the generated folder.
3. After the user downloads files, run `make cnki-intake PROJECT=<project_slug>`; add `BUILD_READERS=1` when the files are PDFs and should immediately become Readers.
4. When you want a full daily recommendation report, run `make cnki-daily PROJECT=<project_slug> TOPIC="主题"`.
5. Open the generated daily report.
6. Read the primary paper with the listed reader or full text.
7. Generate or open the paper context pack when continuing a discussion:

```bash
make paper-context PROJECT=<project_slug> CITEKEY=<citekey>
```

8. Discuss the report questions with Codex.
9. Add the paper's reusable innovations, key limitations, and research
   opportunities to:

```text
projects/<project_slug>/literature/innovation_limitation_bank.md
```

Use this helper to create a blank card if the paper is not in the bank yet:

```bash
make insight-bank PROJECT=<project_slug> CITEKEY=<citekey>
```

10. After real reading, update only the achieved `read_status`.
11. If the paper supports a manuscript claim, add source locators and run:

```bash
make evidence-gate PROJECT=<project_slug>
```

## Evidence Boundary

`cnki-daily` is a recommendation layer. It does not prove that a paper has been
read, verified, or can support a manuscript claim. The evidence gate still
controls manuscript use.
