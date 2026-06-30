# CNKI Workflow

This workflow handles CNKI as a legally authorized literature source.

## Access Boundary

- The user logs in through their own browser, institution VPN, or library portal.
- Do not share CNKI passwords with Codex.
- Codex must not bypass paywalls, CAPTCHA, download limits, or institutional access controls.
- When CAPTCHA, payment, or institutional confirmation appears, the user handles it directly.
- Codex can organize and analyze metadata and full texts that the user is allowed to access.

## Browser Operation Strategy

Use a hybrid route for daily CNKI work:

- Primary browser surface: Codex Chrome extension / `@Chrome`, when available.
  Use it for signed-in CNKI pages, title-click navigation, detail-page `PDF下载`,
  login-state-dependent pages, and occasional UI troubleshooting.
- Primary batch/low-token surface: local scripts. Use scripts to extract result
  rows, click known titles, copy downloaded files, normalize filenames, update
  `library/literature_matrix.csv`, convert CAJ, generate readers, and build
  daily recommendations.
- Fallback GUI surface: Computer Use. Use it only when a task really requires
  operating macOS/Windows UI, such as stubborn save/export dialogs or CAJViewer
  export flows.
- Do not use the in-app `@Browser` as the main CNKI route, because CNKI depends
  on signed-in browser state and institutional access. `@Browser` is better for
  local/public pages that do not require login.

Token rule: keep browser/GUI use narrow and move durable work into local files.
Once CNKI metadata or full text is local, prefer local readers, context packs,
paper briefs, and scripts instead of repeatedly browsing the same CNKI pages.

## Auto Restock

When a project's local CNKI full-text stock falls below the learning threshold,
use the restock command to refill the queue instead of manually picking one
paper at a time:

```bash
make cnki-restock \
  PROJECT=library_short_video \
  MIN_STORED=5 \
  REFILL_COUNT=12 \
  CONFIRM_SAVE=1 \
  ALLOW_NON_PDF=1
```

What it does:

- Counts the project's existing local full texts, including PDF and CAJ-like CNKI files.
- If the count is already at or above `MIN_STORED`, it exits without downloading.
- If the count is below `MIN_STORED`, it ranks unread CNKI rows using the
  project's existing `recommendation_profile.json` and daily recommendation
  stage logic.
- It writes an auditable candidate JSON under `library/cnki_exports/<project>/`
  and then runs the batch downloader against the signed-in Chrome CNKI session.
- Download strategy remains detail-page `PDF下载` first; when
  `ALLOW_NON_PDF=1`, CAJ/NH/KDH download links are accepted as local stock
  fallback instead of being discarded.

This command still does not enter passwords or bypass CAPTCHA, certificate
warnings, institutional login, or subscription barriers. It assumes the user
has already opened CNKI through a legal access route in Chrome.

## Preferred Human Download Handoff

When direct scripted CNKI full-text acquisition is unstable or undesirable, use
the human-in-the-loop handoff. This is now the preferred replenishment pattern
for routine use:

1. Codex prepares CNKI search terms, ranking logic, a download checklist, and a
   target folder.
2. The user opens CNKI through their own legal access route and downloads the
   listed papers into that target folder.
3. Codex validates file types, matches files to citekeys, renames/copies them
   into the stable project library, updates `library/literature_matrix.csv`,
   and optionally builds Readers.

Create a checklist:

```bash
make cnki-handoff \
  PROJECT=library_short_video \
  TOPIC="图书馆短视频相关研究" \
  COUNT=12
```

By default the checklist is strict: a paper must fit the project core terms
instead of merely being a generic short-video paper. If you intentionally want
adjacent comparison papers, add:

```bash
make cnki-handoff PROJECT=library_short_video TOPIC="图书馆短视频相关研究" COUNT=12 ALLOW_EXTERNAL=1
```

Open CNKI advanced search at the same time:

```bash
make cnki-handoff PROJECT=library_short_video TOPIC="图书馆短视频相关研究" COUNT=12 OPEN=1
```

Outputs:

- Browser page: `vault/15_CNKI_Frontier/download_requests/<project>/<date>-<project>-cnki-download-request.html`
- Canonical request note: `vault/15_CNKI_Frontier/download_requests/<project>/<date>-<project>-cnki-download-request.md`
- Machine-readable checklist: `vault/15_CNKI_Frontier/download_requests/<project>/<date>-<project>-cnki-download-request.csv`
- User download folder: `library/pdfs/<project>/incoming/<date>/`

After the user downloads PDFs/CAJ/KDH/NH files into the target folder:

```bash
make cnki-intake PROJECT=library_short_video
```

If the downloaded files are PDFs and Readers should be generated immediately:

```bash
make cnki-intake PROJECT=library_short_video BUILD_READERS=1
```

The intake command rejects fake PDFs whose file extension is `.pdf` but whose
file signature is not `%PDF-`. CAJ/KDH/NH files are accepted as local stock but
should be converted before source-grounded reading:

```bash
make caj-convert PROJECT=library_short_video SCAN=1
```

Use this handoff when the user wants control and visibility. Use `cnki-restock`
only for small, slow, explicitly authorized browser-assisted runs.

## Recommended Flow

1. User opens CNKI through a legal access route.
2. Codex can help formulate Chinese search strings and screening criteria.
3. Export search results from CNKI as CSV, XLSX, RIS, or EndNote text.
4. Put exports under `library/cnki_exports/`.
5. Import with:

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug>
```

6. Generate a daily learning recommendation when the project has a screened
   CNKI matrix:

```bash
make cnki-daily PROJECT=<project_slug> TOPIC="研究主题"
```

7. Download authorized full texts manually through the handoff checklist or
   through the browser session when permitted. Preferred CNKI route:
   - click the paper title in the result list;
   - enter the paper detail / abstract page;
   - click `PDF下载` on the detail page.
   This is preferred because the result-list download button often returns
   `.caj`, while the detail page may expose a direct PDF download.
8. If the detail page has no available `PDF下载`, fall back to the result-list
   download button and treat `.caj` as a convertible full text when legally
   downloaded.
9. Put PDFs/CAJ files under `library/pdfs/` or project-level `literature/pdfs/`.
10. If the file ends in `.caj`, classify and convert it first:

```bash
make caj-convert PROJECT=<project_slug> SCAN=1
make caj-convert PROJECT=<project_slug> CITEKEY=<citekey> UPDATE=1 RUN_READER=1
```

11. If the file is already a PDF, build a source-grounded reader with `make paper-reader PROJECT=<slug> CITEKEY=<citekey> PDF=<path>`.
12. Update `read_status` only after real reading; the CAJ converter and reader command do not mark a paper as human-read automatically.

See `docs/CNKI_DAILY_LEARNING.md` for the daily recommendation and discussion loop.

## Slow Script Download Route

When Chrome UI control is unstable, use the local scripts against the user's
already logged-in Chrome session. Keep runs small and slow:

```bash
make cnki-batch-download \
  PROJECT=library_short_video \
  METADATA=library/cnki_exports/library_short_video/cnki_library_short_video_2026-06-21_top60.json \
  TARGET_TOTAL=60 \
  LIMIT=1 \
  CONFIRM_SAVE=1 \
  PROFILE_FILTER=1 \
  DELAY_MIN=30 \
  DELAY_MAX=45
```

If `LIMIT=1` succeeds, increase to `LIMIT=3` or `LIMIT=5`; avoid starting with
large batches. `PROFILE_FILTER=1` applies the project recommendation profile so
generic short-video papers are skipped unless they match the project terms.

For a manually prepared title list on the current CNKI result page:

```bash
make cnki-download \
  PROJECT=library_short_video \
  TITLES=/path/to/titles.txt \
  MODE=detail-pdf-first \
  CONFIRM_SAVE=1 \
  DELAY_MIN=30 \
  DELAY_MAX=45
```

The scripts may confirm the ordinary macOS save dialog, but they must stop on
CNKI safety verification, CAPTCHA, login, subscription, or permission barriers.
The user handles those pages directly in Chrome, then the script can be resumed
with another small `LIMIT`.

For a safe preview before a real refill run:

```bash
make cnki-restock PROJECT=library_short_video MIN_STORED=5 REFILL_COUNT=12 DRY=1
```

## What The Importer Does

- Adds rows to `library/literature_matrix.csv`.
- Sets `source_database` to `CNKI`.
- Uses deterministic ASCII citekeys like `cnki_2024_<hash>`.
- Keeps CNKI abstracts and keywords in `core_findings` as metadata only.
- Marks `read_status` as `metadata-only`.
- Skips duplicate title/year rows.
- Writes an import report under `library/cnki_exports/import_reports/`.
- Supports `.xlsx` when `pandas` and `openpyxl` are available; legacy `.xls` may require `xlrd`.

## Evidence Gate

Before a CNKI source supports a manuscript claim:

```bash
make cnki-download PROJECT=<project_slug> TITLES=<titles.txt>
make caj-convert PROJECT=<project_slug> CITEKEY=<citekey> UPDATE=1 RUN_READER=1
make paper-reader PROJECT=<project_slug> CITEKEY=<citekey> PDF=<authorized_pdf>
make evidence-gate PROJECT=<project_slug>
```

`metadata-only`, `abstract-only`, `ai-summarized`, `unread`, or blank read statuses cannot satisfy manuscript evidence. A source used in `07_claim_evidence_map.md` or `manuscript/paper.md` should be `human-read` or `verified` and have `pdf_path`, `note_path`, or `literature/readers/<citekey>/paper.md`.

## What Still Needs Human Judgment

- Whether the paper is CSSCI, 北大核心, or relevant to 《图书情报工作》.
- Whether the full text was actually read.
- Whether a source supports a specific manuscript claim.
- Whether a downloaded full text is legally usable in the project.
