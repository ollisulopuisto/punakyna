# Agent instructions

- Read README.md, ROADMAP.md and TODO.md before starting work.
- All changes as PRs. Never push to main directly. Never merge; the human merges.
- Run `python -m pytest tests/` and `python eval/evaluate.py` before opening a PR.
  Evaluate.py output goes into the PR description; note it is a smoke test,
  not a held-out benchmark.
- Document your work here and in TODO.md (what was done, what is next).
- Bolt (2026): Suorituskykyoptimointi tehty `punakyna/pipeline.py`:ssa token-luonnille (_PipelineToken slots-luokka korvasi dynaamisen type()-kutsun).
- Bolt (2026-11-05): Suorituskykyoptimointi tehty `punakyna/pipeline.py`:ssa `_spelling_suggestions`- ja span-seurannalle (`_DIGITS.isdisjoint`, `tok.lower`-uudelleenkäyttö ja `startswith`-offset-seuranta korvasivat generaattori- ja `.find()`-kutsut; monikappaletekstin latenssi -42,5 %).
- Bolt (2026-11-05): Suorituskykyoptimointi tehty `punakyna/rules.py`:ssa säännölle `check_olla_agreement` (varhainen poistuminen `_OLLA_3RD_PRES`-tarkistuksella ennen kalliita `_analyze`-kutsuja; sääntökohtainen suoritusnopeutus ~79 %).
- Bolt (2026-11-06): Suorituskykyoptimointi tehty `punakyna/rules.py`:ssa säännölle `check_double_word` (varhainen poistuminen `prev.lower != cur.lower` ennen merkkijonoviipalointia, `.strip()`-kutsua ja `isupper()`-tarkistuksia; sääntökohtainen suoritusnopeutus ~61,7 %).
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

## 2026-11-05: Host header validation hardening (Sentinel)

- Hardened `_valid_host_header` in `punakyna/api.py` with strict regex and port range check (`1..65535`).
- Fixes handling of standard IPv6 loopback `[::1]` and `::1` without ports.
- Rejects malformed host headers with non-numeric ports (e.g. `127.0.0.1:evil`), out-of-range ports, and userinfo.
- Added regression tests in `tests/test_api_hardening.py`.

## 2026-11-07: Security response headers enhancement (Sentinel)

- Added defense-in-depth HTTP security headers (`X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`) to all server responses in `punakyna/api.py`.
- Protects clients and browsers from MIME type sniffing and iframe framing / UI redressing.
- Added regression tests in `tests/test_api_hardening.py`.

## 2026-11-07: PERFECT_PASSIVE_PARTICIPLE (v0.1.1)

- Miss reported by Olli in LibreOffice: "Minä olen menty kotiin." was not flagged
  (Voikko GC and existing rules do not check the participle type after olla).
- New rule PERFECT_PASSIVE_PARTICIPLE: olen/olet/olemme/olette/ovat (and past
  forms; "en ole" after a person negation) + a word analysed only as a passive
  TU participle of a listed intransitive verb -> suggest the NUT participle.
  Sources: VISK §1292 (passive perfect: auxiliary in 3rd person singular),
  VISK §530 (intransitive passive participles occur only in compound forms).
- Deliberately limited to a fixed intransitive verb list: transitive TU
  participles are valid predicatives ("olen kiusattu", "olemme tehty puusta").
  "on menty", "kotiin on menty", "ei ole menty" are not flagged.
- Tests: tests/test_perfect_passive_participle.py; smoke eval 26 error / 30 clean, 0 false alarms.
- Env note: test_lo_writer_gui and test_lo_xproofreader fail in this Linux sandbox
  (unopkg install fails; also fails on unmodified main for the GUI test).
- Version bumped to 0.1.1 (pyproject, __init__, description.xml, browser manifest, uv.lock). No OXT built.

## 2026-11-07: rule registry (v0.1.2, stacked on PR #19)

- Added punakyna/registry.py (id, category, layer, severity, sources, source
  status, tests per rule) and scripts/gen_coverage_map.py -> docs/coverage-map.md.
- tests/test_registry.py: every emitted rule id is registered, sourced and has
  an existing test module; map must be regenerated when the registry changes.
- No behaviour change. Source status 'chapter' (DOUBLE_WORD) and in-code VISK
  citations older than this registry (e.g. §1581, §1284c in rules.py) are not
  yet re-verified. Next: generalise participle/agreement rules (inventory cat. 1-2).
- New rules must add a RuleSpec with a verified source before merging.

## 2026-11-07: LibreOffice extension update feed (Olli: "native Libre office way")

- description.xml now has update-information pointing at
  https://github.com/ollisulopuisto/punakyna/releases/latest/download/punakyna.update.xml
  (LibreOffice's own extension updater; Sparkle does not apply to an OXT).
- make_update_xml.py writes the feed from description.xml's version and a release tag.
  .github/workflows/update-feed.yml attaches it to published full releases that carry
  punakyna-full-macos.oxt. Draft and pre-release candidates (what build-full-oxt makes)
  never reach /releases/latest, so testers are not auto-updated. Free: ubuntu runner on a
  public repo, one small release asset.
- A new OXT version must raise the version in description.xml, or LibreOffice sees no update.
- Not verified on a Mac: LibreOffice's Check for Updates against a real published release.
- Version bumped to 0.1.3 (pyproject, __init__, description.xml, browser manifest, uv.lock); chain: 0.1.1 #19, 0.1.2 #21, 0.1.3 this PR.

## 2026-11-07: participle/agreement generalisation (v0.1.4, inventory step 2)

- PERFECT_PASSIVE_PARTICIPLE: verb table widened from 21 to 33 intransitives.
  tests/test_sg_subject_plural_verb.py checks every table entry against Voikko
  (sg and pl NUT forms exist and belong to the verb), so the table cannot rot.
- New SV_NUMBER_NONOLLA (severity `warning`, VISK §1267, §1270, §1272): singular
  nominative-only noun immediately before a 3rd-person plural finite verb that is
  not olla ("Lapsi leikkivät"). Only this direction: plural subject + singular
  verb ("lapset leikkii") is common speech and is deliberately not flagged.
  Guards: coordination (also across ordinal-dot sentence splits, via new
  `before` context passed to run_rules), possessive suffix (Voikko POSSESSIVE),
  collective proper names, kaikki/moni/jokainen, olla (copula agrees with predicative).
- Precision check: unmodified Wikipedia sweep of 16+8 fi.wikipedia articles
  (~77k words, 2026-11-07): 0 flags from both rules after fixing three false
  positives found on the first pass (ordinal coordination x2, copula). Not a
  held-out benchmark. Smoke eval: 0 false alarms on 32 clean sentences.
- Not done (needs parser or contested norm): plural subject + singular verb,
  predicative agreement (cat. 4), numeral + noun (cat. 8): next steps.
- Version 0.1.4 (pyproject, __init__, description.xml, browser manifest, uv.lock).

## 2026-11-07: numeral + noun case (v0.1.5, inventory step 3a)

- New NUM_NOUN_CASE (warning, VISK §789, §773): cardinal 2-19 as a separate
  nominative word + noun analysed only as singular nominative common noun
  ("kolme lapsi" -> "kolme lasta"). No automatic replacement (no generator).
- Skipped on purpose: digits (years, model numbers: "2020 syksy"), kuusi (also
  the tree), sata/tuhat/miljoona, capitalised nouns, kello/klo/numero/luku/sivu/
  kohta/vuonna + numeral, coordination (ja/tai/sekä), possessive suffix, names.
- Precision: 0 flags on the ~77k-word fi.wikipedia sweep; smoke eval 0 false alarms
  on 34 clean sentences. Not a held-out benchmark; recall on real writer errors unknown.
- Version 0.1.5. Next: predicative agreement (cat. 4), style profile config.
