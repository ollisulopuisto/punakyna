## 2026-11-03 - Path Traversal in Per-App Token Revocation
**Vulnerability:** Application token identifiers were joined directly to directory paths in file deletion routines without path validation, allowing directory traversal sequences to target files outside the tokens directory.
**Learning:** Functions that manage file lifecycles (like revocation or deletion) often assume valid identifier inputs if creation functions perform checks, leading to security oversights when deletion routines omit input validation.
**Prevention:** Centralize path and identifier validation across all lifecycle operations (create, read, delete), reject directory traversal characters explicitly, and verify resolved paths remain confined to the intended base directory.

## 2026-11-05 - Incomplete Application Identifier Validation via Blocklists
**Vulnerability:** Application identifiers in token management relied on a character blocklist (`/`, `\`, `\0`, `.`, `..`), allowing control characters (CRLF), leading dots, and oversized strings to create malformed token files and corrupt CLI listings.
**Learning:** Blocklists in path and identifier validation fail to protect against non-printable or whitespace characters, leading to injection or hidden file creation within credential storage directories.
**Prevention:** Use strict allowlists (e.g. `^[a-zA-Z0-9](?:[a-zA-Z0-9_\-\.]{0,62}[a-zA-Z0-9])?$`) for all resource identifiers stored on the filesystem.
