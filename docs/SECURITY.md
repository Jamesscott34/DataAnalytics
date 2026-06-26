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
- Files larger than 50 MB require browser-side SHA-256 calculation and user
  confirmation before upload.
- When the browser sends a SHA-256 hash, the backend recomputes the hash and
  rejects the upload if the values do not match.
- Scanner results are persisted in the `security_scans` table.
- The frontend displays scanner status, risk score, issues, and recommended
  action after upload.

## Large File Handling

The default absolute upload cap is 250 MB. Files above the 50 MB verification
threshold are still allowed when they pass validation and scanner checks, but
the user must inspect and confirm the browser-computed SHA-256 hash first.

The backend remains the source of truth: it calculates its own SHA-256 hash,
compares it with the browser value when provided, applies strict CSV and
scanner rules, then returns the final hash and scan status to the GUI.

## Watched Folder Integrity Manifest

On backend startup the application scans `temp_assets/` and `assets/`, computes
SHA-256 hashes for every file, and compares them against a password-protected
encrypted manifest stored at `backend/data/asset_manifest.enc`.

- First run: analysts create a manifest password and all discovered files are
  recorded.
- Later runs: the user unlocks the manifest once per server session (and once
  per browser session) so the UI can report new, modified, or removed files.
- Approved changes are written back to the encrypted manifest after explicit
  user confirmation in the GUI.

## Limitations

This scanner is not a replacement for production malware scanning, sandboxing,
data-loss prevention, or human review of sensitive datasets. Do not upload
private, regulated, or production datasets unless the deployment environment is
designed and approved for that data.
