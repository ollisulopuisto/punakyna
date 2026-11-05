# Agent instructions

- Read README.md, ROADMAP.md and TODO.md before starting work.
- All changes as PRs. Never push to main directly. Never merge; the human merges.
- Run `python -m pytest tests/` and `python eval/evaluate.py` before opening a PR.
  Evaluate.py output goes into the PR description; note it is a smoke test,
  not a held-out benchmark.
- Document your work here and in TODO.md (what was done, what is next).
- Bolt (2026): Suorituskykyoptimointi tehty `punakyna/pipeline.py`:ssa token-luonnille (_PipelineToken slots-luokka korvasi dynaamisen type()-kutsun).
- Precision first: a new rule must not add false alarms on eval/smoke_clean.jsonl.
  If a rule cannot be made clean-set-safe, leave it out or mark it severity=info.
- Finnish user-facing strings are checked against Kielitoimiston sanakirja
  (kielitoimistonsanakirja.fi); do not invent "corrections" without a source.
- Do not add third-party model weights or datasets to the repo. License
  status of FinnGEC weights/data is unresolved; see README section Neurotaso.

## 2026-11-04: bundled extension stack recovery

- Integrated the surviving #9 merge commit from local-oxt onto current main,
  preserving #5 description/setup hints, #6 project metadata and lockfile,
  and #7 server preflight. #8 had closed without bringing the engine to main.
- Packaging workflow is now manual-only: no automatic Actions builds or
  uploads while account-wide artifact-storage cost clearance is pending.
- macOS LibreOffice integration and correction application remain unverified;
  the already-delivered bundled test package still awaits the user's test.
- See the integration PR for local test/evaluation results and environment
  limitations. No agent merge to main or replacement package release.

## 2026-11-05: bundled Mac crash investigation

- Shipped OXT failed on Mac: CODESIGNING Invalid Page during native dlopen.
  All eleven shipped dylibs have a stale page-zero CodeDirectory hash after
  install_name_tool. Sign final staged bytes and verify before packing.
- Added final-OXT signature-page verification and an opt-in actual arm64
  LibreOffice.app/UNO host harness. The harness must not count Linux/unit
  passes as Mac validation. F7/underline/UI correction remain a GUI gate.
- No replacement package built or uploaded during the artifact-cost hold.

## 2026-11-05: optional style advice

- Added opt-in actor clarity and explicit narrator/reader consistency profiles.
- Local only, no auto-rewrites; ambiguous and quoted/code-like text skipped.
- Added CLI/API profile and Writer settings dialog; grammar diagnostics win.
- Full Linux suite: 142 passed, 6 skipped (final style branch).
- Baseline smoke: unchanged detections, 0 unexpected flags / 28 clean sentences.
- Installed Linux UNO menu/dialog visually checked; Save and subsequent callback pass.
- Mac settings/menu GUI still unverified. No release or human merge performed.
- Details and deliberate gaps: docs/style-advice.md.

## 2026-11-05: token management hardening (Sentinel)

- Replaced blocklist with strict allowlist regex validation for application
  identifiers in tokenfile.py (`^[a-zA-Z0-9](?:[a-zA-Z0-9_\-\.]{0,62}[a-zA-Z0-9])?$`).
- Rejects control characters (CRLF), leading/trailing dots, spaces, and length > 64.
- Added comprehensive regression tests in `tests/test_api_hardening.py`.
- Full suite (134 passed, 15 skipped) and smoke evaluation (0 false alarms) pass.
