## 2026-11-03 - Path Traversal in Per-App Token Revocation
**Vulnerability:** Application token identifiers were joined directly to directory paths in file deletion routines without path validation, allowing directory traversal sequences to target files outside the tokens directory.
**Learning:** Functions that manage file lifecycles (like revocation or deletion) often assume valid identifier inputs if creation functions perform checks, leading to security oversights when deletion routines omit input validation.
**Prevention:** Centralize path and identifier validation across all lifecycle operations (create, read, delete), reject directory traversal characters explicitly, and verify resolved paths remain confined to the intended base directory.

## 2026-11-05 - Incomplete Application Identifier Validation via Blocklists
**Vulnerability:** Application identifiers in token management relied on a character blocklist (`/`, `\`, `\0`, `.`, `..`), allowing control characters (CRLF), leading dots, and oversized strings to create malformed token files and corrupt CLI listings.
**Learning:** Blocklists in path and identifier validation fail to protect against non-printable or whitespace characters, leading to injection or hidden file creation within credential storage directories.
**Prevention:** Use strict allowlists (e.g. `^[a-zA-Z0-9](?:[a-zA-Z0-9_\-\.]{0,62}[a-zA-Z0-9])?$`) for all resource identifiers stored on the filesystem.

## 2026-11-05 - Flawed Host Header Parsing and Validation in DNS Rebinding Defense
**Vulnerability:** Host header validation for DNS rebinding protection used naive string splitting on `:` without validating the port number or distinguishing IPv6 brackets, allowing malformed non-numeric ports (e.g., `127.0.0.1:evil`) and rejecting valid IPv6 loopback without ports (`[::1]`).
**Learning:** Naive splitting on `:` breaks IPv6 address parsing and allows arbitrary suffixes in the port section if port format and numerical ranges (1-65535) are not verified.
**Prevention:** Parse network addresses with structured regex or standard authority parsers that strictly validate host identity and enforce numeric port ranges (1-65535).
