# Git Backup Strategy

Last updated: 2026-06-29

This workflow uses a two-layer backup model:

1. Git tracks text, structure, scripts, configuration, dashboards, notes, CSV registries, and project state.
2. Lightweight zip backups capture critical daily state for quick local restore.

Large source files stay outside Git: PDFs, CAJ/KDH files, raw data, exported office files, preview images, videos, caches, and zip backups.

## Why This Split

Git is best for:

- Seeing exactly what changed each day.
- Restoring a specific file or section from an earlier commit.
- Syncing the text workflow to a private remote repository.
- Reviewing long-term evolution of research questions, cards, scripts, and logs.

Git is not best for:

- Storing large PDFs or CAJ files.
- Storing daily zip backups.
- Storing generated binary previews or raw datasets.

Those large files should stay local, in institutional storage, iCloud/Drive, an external disk, or a dedicated data archive.

## Daily Command

Use this after a daily paper run or any substantial workflow change:

```bash
make workflow-refresh-git DATE=2026-06-29 NOTE="daily closeout"
```

It runs the normal closeout, creates a local backup zip, updates logs/compact summaries/audit pages, commits trackable text assets, pushes to the private remote, refreshes Git health, then commits that final audit state.

If you only want local refresh without Git:

```bash
make workflow-refresh DATE=2026-06-29 NOTE="daily closeout"
```

If you only want a Git snapshot:

```bash
make git-snapshot DATE=2026-06-29 NOTE="manual snapshot" PUSH=1
```

## Storage Policy

Tracked by Git:

- `scripts/`, `docs/`, `config/`, `prompts/`
- `vault/**/*.md`, `vault/**/*.csv`
- `projects/**/*.md`, `projects/**/*.csv`, `projects/**/*.yaml`
- `library/literature_matrix.csv` and small literature registries
- `study_dashboard.html`, `workflow_health.html`, `paper_reading/*.html`, `knowledge_graph/index.html`, `logs/index.html`

Not tracked by Git:

- `backups/*.zip`
- `library/pdfs/`, `library/papers/`, `library/text/`
- `*.pdf`, `*.caj`, `*.kdh`
- generated preview images and office exports
- raw/interim/processed project data
- caches such as `.DS_Store`, `__pycache__`, `.ipynb_checkpoints`

## Local Backup Retention

Backups are intentionally local and ignored by Git.

Create a backup:

```bash
make workflow-backup DATE=2026-06-29 NOTE="daily closeout"
```

Create a backup and keep only the newest 30 backup zips:

```bash
make workflow-backup DATE=2026-06-29 NOTE="daily closeout" KEEP=30
```

Prune without creating a new backup:

```bash
make workflow-backup-prune KEEP=30
```

Pruning is explicit because the workflow should not delete user files silently.

## Restore Basics

View recent commits:

```bash
git log --oneline --decorate -10
```

Restore one file from a previous commit:

```bash
git checkout <commit-hash> -- path/to/file
```

Restore a local zip snapshot by opening `backups/index.html`, selecting the desired package, and extracting only the needed files.

## Health Check

Run:

```bash
make workflow-audit DATE=2026-06-29
```

The health page checks:

- Whether Git is initialized.
- Whether `origin` exists.
- Whether local changes are uncommitted.
- Whether local commits are still unpushed.
- Whether local zip backups are recent.
