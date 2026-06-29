# CNKI Frontier

This folder stores CNKI-based learning and discussion artifacts.

## Folders

- `digests/`: 5-7 paper frontier radar digests generated from CNKI metadata.
- `daily_recommendations/`: one primary paper per active research day, with
  companion papers, reading route, and discussion questions.
- `paper_briefs/`: one-paper discussion cards generated from a matrix citekey.

## Commands

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug>
make cnki-frontier TAG=<project_slug> TOPIC="主题"
make cnki-daily PROJECT=<project_slug> TOPIC="主题"
make paper-brief CITEKEY=<citekey>
```

## Reading Levels

- `metadata-only`: title/abstract/keywords only; useful for screening, not for citation support.
- `skimmed`: user or Codex has skimmed accessible full text.
- `human-read`: user has read the full text.
- `verified`: claim-level evidence has source locator and can support manuscript writing.

Do not use `metadata-only` papers as evidence for manuscript claims.
