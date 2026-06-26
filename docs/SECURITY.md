# Security

## Python-Only Upload Scanner

The upload scanner is a defensive validation layer written in Python. It is
not antivirus and does not detect novel malware, scan archives, inspect macros,
or guarantee that a file is safe.

The scanner currently checks uploaded CSV files for:

- Unsafe filenames and path traversal attempts.
- Non-CSV or executable-style extensions.
- Null bytes and binary-like content.
- Invalid or suspicious text encoding.
- Unusually long rows.
- HTML/script injection markers such as `<script>`, `javascript:`, `onerror=`,
  `onclick=`, `<iframe>`, `<object>`, and `<embed>`.
- CSV formula injection cells beginning with `=`, `+`, `-`, or `@`.
- Dangerous spreadsheet formulas including `=CMD`, `=HYPERLINK`,
  `=WEBSERVICE`, and `=IMPORTXML`.
- Suspicious command strings including `cmd.exe`, `powershell`, `bash -i`,
  `nc -e`, `wget`, and `curl`.
- Embedded URLs.
- Long base64-like payloads.

## Status Meanings

- `safe`: no scanner issues found.
- `warning`: suspicious content exists, but the file may be analysable after
  review and cleaning.
- `blocked`: the file contains high-risk or unsafe content and should not be
  analysed.

## Current Controls

- Uploaded files are stored outside the frontend public directory.
- Uploads require an authenticated Admin or Analyst user.
- The API stores a SHA-256 hash for deduplication.
- Scanner results are persisted in the `security_scans` table.
- The frontend displays scanner status, risk score, issues, and recommended
  action after upload.

## Limitations

This scanner is not a replacement for production malware scanning, sandboxing,
data-loss prevention, or human review of sensitive datasets. Do not upload
private, regulated, or production datasets unless the deployment environment is
designed and approved for that data.
