# CNKI Exports

Put CNKI-exported metadata files here.

Preferred export formats:

- CSV or tab-delimited text
- Excel `.xlsx` when the local Python environment has `pandas` and `openpyxl`
- RIS
- EndNote text (`.enw` or tagged `.txt`)

Legacy `.xls` may require `xlrd`. If an Excel file fails, export as
CSV/RIS/EndNote text or install the missing backend.

Import command:

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug>
```

Dry run:

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug> DRY=1
```

Reports are written to `library/cnki_exports/import_reports/`.
