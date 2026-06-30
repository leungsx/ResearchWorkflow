# CNKI Intake Report - library_short_video

Request: `vault/15_CNKI_Frontier/download_requests/library_short_video/2026-06-30-library_short_video-cnki-download-request.csv`
Incoming folder: `library/pdfs/library_short_video/incoming/2026-06-30`
Target folder: `library/pdfs/library_short_video`

- Stored: 0
- Readers built: 0
- Needs CAJ/KDH/NH conversion: 0
- Invalid PDF downloads: 0

Next commands:

```bash
make caj-convert PROJECT=library_short_video SCAN=1
make cnki-daily PROJECT=library_short_video
make learning-dashboard
```
