# CAJ Conversion Workflow

This workflow handles CNKI files whose filename ends in `.caj`.

## Why This Exists

CNKI downloads can produce two different local cases:

- A file named `.caj` that is actually a PDF. It starts with `%PDF-` and can be read directly after copying/renaming to `.pdf`.
- A true CAJ/KDH file. In the current pilot these start with `KDH 2.00 Copyright(C) 2000 CAJCD` and need a converter or an authorized CNKI/CAJViewer export route before `paper-reader` can process them.

## Legal Boundary

- Files must come from the user's authorized CNKI / library / institutional access.
- Codex must not bypass CNKI CAPTCHA, paywalls, download limits, or access controls.
- Do not upload private or unpublished documents to third-party conversion services without explicit consent.

## Commands

Scan a project and classify `.caj` files:

```bash
make caj-convert PROJECT=library_short_video SCAN=1
```

Convert one citekey when possible:

```bash
make caj-convert PROJECT=library_short_video CITEKEY=cnki_2020_64b4f881c9
```

Convert, update the literature matrix to the converted PDF path, and build a reader:

```bash
make caj-convert PROJECT=library_short_video CITEKEY=cnki_2020_64b4f881c9 UPDATE=1 RUN_READER=1
```

Convert all project-tagged rows with local `.caj` paths:

```bash
make caj-convert PROJECT=library_short_video ALL=1
```

## Outputs

- Converted PDFs: `library/pdfs/<project>/converted/<citekey>.pdf`
- Conversion reports: `projects/<project>/literature/caj_conversion/<citekey>.md`
- First-page preview PNGs when Poppler is available: `projects/<project>/literature/caj_conversion/<citekey>_preview/page-1.png`
- Reader packages when `RUN_READER=1`: `projects/<project>/literature/readers/<citekey>/`

## Converter Dependency

The script first handles PDF-in-CAJ-extension files without external dependencies. True CAJ/KDH files need a converter.

Preferred local route:

- Install MuPDF so `mutool` is available.
- Clone or install `caj2pdf/caj2pdf`.
- Keep the converter at `tools/caj2pdf/caj2pdf`, or set `CAJ2PDF_BIN=/path/to/caj2pdf`.

The open-source `caj2pdf` route only supports some CAJ variants. If it fails, use an authorized CNKI/CAJViewer export or print-to-PDF route, then run `make paper-reader` on the exported PDF.

## Current Pilot Notes

For `library_short_video`, `make caj-convert PROJECT=library_short_video SCAN=1` currently identifies:

- true KDH/CAJ: `cnki_2021_d35f8e895a`, `cnki_2021_dfab60236e`, `cnki_2020_64b4f881c9`, `cnki_2023_34348faa1e`
- PDF despite `.caj` extension: `cnki_2020_2a150c6df8`, `cnki_2021_7556aafa99`, `cnki_2021_5530e86157`

The first two true KDH/CAJ files already have HTML-route readers. The unresolved reader gaps are `cnki_2020_64b4f881c9` and `cnki_2023_34348faa1e`.
