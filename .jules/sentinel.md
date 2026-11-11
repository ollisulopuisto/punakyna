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

## 2026-11-07 - Missing Defense-in-Depth HTTP Response Security Headers
**Vulnerability:** The local loopback HTTP server omitted standard security headers (`X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`), leaving browser interactions reliant solely on content-type enforcement and lack of CORS headers.
**Learning:** Even loopback servers communicating via JSON can be probed or embedded by web applications running in local browsers if additional browser-level security headers are missing.
**Prevention:** Always set `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` on all responses (including errors) in HTTP servers to reinforce defense in depth.

## 2026-11-09 - Inconsistent Identifier Validation During Credential Enumeration
**Vulnerability:** `load_all_tokens` enumerated files in the token directory without validating filename identifiers against the application allowlist (`_validate_app_name`), allowing hidden or malformed token files to authenticate requests while being unrevocable via standard management routines.
**Learning:** Directory-based credential loaders must enforce the exact same naming and format constraints as creation and revocation functions, otherwise orphaned or malformed credentials can persist and authenticate while evading management tooling.
**Prevention:** Always apply the resource identifier validation function across directory enumeration and bulk-loading routines.

## 2026-11-09 - Client-Side Loopback Target Validation
**Vulnerability:** Client adapter library accepted arbitrary destination host parameters, allowing bearer authentication tokens and document content to be dispatched over network connections to external addresses if configured with an untrusted host.
**Learning:** Hardening server endpoints to bind exclusively to loopback addresses only protects inbound access; client connection utilities must enforce matching boundary checks so credentials and private text cannot be directed outbound to external endpoints.
**Prevention:** Validate destination hosts against strict loopback allowlists on client libraries that transmit local authentication tokens or sensitive user payloads.

## 2026-11-10 - Connection Desynchronization on Invalid Request Framing Headers
**Vulnerability:** When requests contained invalid framing headers such as non-numeric Content-Length, error responses were returned without closing the underlying connection, leaving unread body bytes to desynchronize subsequent HTTP pipelined requests.
**Learning:** Any request header error that affects framing boundaries makes calculating the remainder of the request body impossible; persistent connections must always be terminated immediately upon encountering malformed framing metadata.
**Prevention:** Immediately drain available bytes, mark connections for closure, and emit `Connection: close` whenever request framing headers fail validation.
