## 2026-11-03 - Path Traversal in Per-App Token Revocation
**Vulnerability:** Application token identifiers were joined directly to directory paths in file deletion routines without path validation, allowing directory traversal sequences to target files outside the tokens directory.
**Learning:** Functions that manage file lifecycles (like revocation or deletion) often assume valid identifier inputs if creation functions perform checks, leading to security oversights when deletion routines omit input validation.
**Prevention:** Centralize path and identifier validation across all lifecycle operations (create, read, delete), reject directory traversal characters explicitly, and verify resolved paths remain confined to the intended base directory.
