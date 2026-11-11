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
- Bolt (2026-11-07): Suorituskykyoptimointi tehty `punakyna/rules.py`:ssa säännölle `check_attribute_agreement` (varhainen poistuminen `if not a_num: continue` ennen toisen sanan `_analyze`- ja `_only_noun_number`-kutsuja; sääntökohtainen suoritusnopeutus ~26,7 %, koko putken latenssi -6,6 %).
- Bolt (2026-11-08): Suorituskykyoptimointi tehty `punakyna/rules.py`:ssa säännölle `check_typography` (merkkisisältötarkistukset `in` ennen regex-hakuja `%`, `€/$ /£`, `.` ja `-`; sääntökohtainen suoritusnopeutus ~64,0 %, koko putken latenssi -11,3 %).
- Bolt (2026-11-09): Suorituskykyoptimointi tehty `punakyna/pipeline.py`:ssa oikeinkirjoitustarkistukselle (`_spelling_suggestions` tallentaa ja lukee `voikko.spell`-tulokset dokumenttikohtaiseen `spell_cache`-sanakirjaan; sääntökohtainen suoritusnopeutus ~60,1 %, koko putken latenssi -11,2 %).
- Bolt (2026-11-10): Suorituskykyoptimointi tehty `punakyna/rules.py`:ssa säännölle `check_active_perfect_passive_participle` (varhainen poistuminen `if not nxt.lower.endswith(('tu', 'ty')):` ennen `_analyze`- ja `_passive_only_participle_verb`-kutsuja; sääntökohtainen suoritusnopeutus ~77,5 %).
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

## 2026-11-08: Fallback error handling & server banner hardening (Sentinel)

- Overrode `send_error` in `punakyna/api.py` to return JSON error responses with defense-in-depth security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`) instead of default HTML error responses.
- Overrode `version_string` in `Handler` to emit only `Punakyna/0.5` without disclosing backend runtime platform/Python version.
- Added regression tests in `tests/test_api_hardening.py`.

## 2026-11-09: Token loading application identifier validation (Sentinel)

- Enforced `_validate_app_name` in `load_all_tokens` (`punakyna/tokenfile.py`) so token files in `tokens/` whose names fail application identifier validation (e.g. hidden files, non-allowlist filenames) are safely ignored.
- Prevents unrevocable or hidden token files from authenticating API requests.
- Added regression tests in `tests/test_api_hardening.py`.

## 2026-11-09: Client loopback destination host validation (Sentinel)

- Enforced loopback host validation in `punakyna/client.py` (`check`): rejects non-loopback destination hosts with `ValueError`.
- Ensures bearer authentication tokens and document content are never dispatched to external network endpoints.
- Added regression tests in `tests/test_client.py`.

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
## 2026-11-07: style profile: sentence length, virkakieli preset (v0.1.6, inventory S1)

- StyleProfile.max_sentence_words (0 off), STYLE_SENTENCE_LENGTH, preset('virkakieli'),
  CLI --max-sentence-words / --profile. Sources: Kotus virkakielivinkki and
  Kielitoimiston ohjepankki "Pitkät virkkeet" (read 2026-11-07): 15 words, no
  absolute limit. Opt-in only; never `error`.
- Style rule ids (STYLE_*) now in the registry; test_registry also scans
  positional Suggestion('ID', ...) constructors. STYLE_PERSON has only a chapter-level source.
- Not done: LibreOffice settings dialog field, selkokieli preset (Selkokeskus gives
  no numeric threshold I could verify), nominal style / wordiness rules.
- Version 0.1.6.

## 2026-11-07: attribute agreement (v0.1.7, inventory step 4a)

- ATTR_AGREEMENT: adjective attribute and noun in nominative disagree in number
  ("isot talo" -> "isot talot"). Sources: VISK §1302 (etumääritteet kongruoivat
  luvussa ja sijassa), §582. No automatic replacement.
- Skipped on purpose: participles (Voikko tags nähnyt/ollut as adjectives), names,
  quantifier-like words (moni, useat, muut, eri ...), "itse", non-nominative cases,
  anything with ambiguous analyses, punctuation between the words.
- Found while building: a first version flagged "nähneensä sävelet" and "suomalaiset itse"
  on the wiki sweep; both fixed. Now 0 flags on the ~77k-word sweep and 0/34 on the clean smoke set.
- Predicative (post-copula) agreement stays with the parser tier (PRED_NUM).
- Version 0.1.7.

## 2026-11-07: typography rules from the ohjepankki (v0.1.8)

- New: TYPO_PERCENT_SPACE, TYPO_CURRENCY_SPACE, TYPO_CLOCK_FORMAT (style), TYPO_ABBR_DOT.
  Sources are the four ohjepankki pages in the registry (read directly). Page text is not
  copied; docs/ohjepankki-candidates.md has our paraphrased candidate list for the whole site.
- Licence: the ohjepankki footer says CC BY-NC-ND 4.0, so the repo holds links and our own
  paraphrase only. The crawled datasets (ohjepankki 729 pages, VISK partial) are private.
- libvoikko splits sentences at "9:" in "klo 9:15", so the clock check runs on the whole text
  in the pipeline instead of per sentence.
- Precision: 1 hit on the ~77k-word Wikipedia sweep ("Kello 10:45", a true instance of the
  style advice), 0 on the clean smoke set.
- This PR is stacked on #26 (ATTR_AGREEMENT, v0.1.7). Version 0.1.8.

## 2026-11-08: API fallback fixes after review of #29 (v0.1.9)

- send_error override (from #29) left HTTP/1.1 connections open with the request body unread, so
  leftover bytes became the next request ("junkGET" -> a second 501). It now sets
  close_connection and sends Connection: close, like the standard handler.
- HEAD with no handler wrote the JSON body. _send now skips the body for HEAD, keeping Content-Length.
- Raw-socket regression tests in tests/test_api_hardening.py (fail on unfixed code).

## 2026-11-08: opt-in debug logging for the LibreOffice adapter (v0.1.11)
- punakyna/debuglog.py: off by default. ~/.config/punakyna/debug.json (read per call) or PUNAKYNA_DEBUG=1. Options: log (JSONL to <tmpdir>/punakyna-debug.log, 5 MB cap, includes the document text), error_type ("proofreading" default | "spelling" experiment), drop_suggestions.
- Purpose: diagnose the blue smear in LibreOffice's Spelling dialog on macOS (hypothesis: grammar-type error rendering; unproven). Default behaviour unchanged.
## 2026-11-08: TYPO_DECIMAL_POINT (v0.1.10)
- New rule TYPO_DECIMAL_POINT (warning): `3.5 kg` -> `3,5 kg`. Source: https://kielitoimistonohjepankki.fi/ohje/luvut-ja-numerot-desimaaliluvut/ (read directly; SFS 4175, "desimaalipistettä ei suositella suomenkielisiin teksteihin").
- Deliberately narrow: fires only on `N.N` (1-3 digits, 1-2 decimals) directly followed by a unit (%, °C, kg, km, euroa, ...). Dates, clock times, section numbers, versions, IPs, thousands grouping (1.000) and the sports-time form 2.19,03 are not flagged.
- Tests in tests/test_typography.py; wiki sweep (~77k words): 0 hits.

## 2026-11-08: Update feed moved to a fixed release (v0.1.12)
- Olli's LibreOffice "Check for Updates" showed "releases/latest/download/punakyna.update.xml does not exist": every release here is a draft or pre-release, and /releases/latest never resolves to those.
- description.xml now points at https://github.com/ollisulopuisto/punakyna/releases/download/update-feed/punakyna.update.xml (fixed tag `update-feed`).
- update-feed.yml: on a published (non-draft, pre-releases included) release that carries punakyna-full-macos.oxt, regenerate the feed for that tag and upload it to the `update-feed` release, creating it on first run. Drafts do not fire the event, so nothing updates until Olli publishes a release.
- Already-installed OXTs (0.1.11 and older) keep the old URL; only an OXT built from this version on checks the new one. Needs a version bump in each new OXT or LibreOffice sees no update.
- Not verified on a Mac: the real Check for Updates against a published release.

## 2026-11-08: TYPO_RANGE_HYPHEN (v0.1.13)

- New rule TYPO_RANGE_HYPHEN (warning): `20-30` -> `20–30` (ajatusviiva). Source:
  ohjepankki "Ajatusviiva: rajakohdat ja osapuolet" (read 2026-11-08):
  ajatusviiva lukujen rajakohdissa ja osapuolten tuloksissa ("9–12", "2–1").
- Deliberately narrow: flags only pairs where either number is 1-2 digits
  ("16-20", "2-1") or a 4-digit year 1800-2199 ("1853-1862"). Skipped on
  purpose: 3+3-digit pairs (model numbers "737-800" vs ranges "305-310 km" -
  the latter is a known recall gap), "56-3" series models, letter-adjacent
  codes (UTF-8), URL-encoded filenames (%28...), chain identifiers
  (ISBN 978-951-..., ISO dates 2026-11-08) and ISSN/ISBN/DOI contexts.
- Precision: wiki sweep (24 fi.wikipedia articles, ~80k words): 9 hits, all
  true instances of hyphen-for-en-dash (year ranges, page spans, placements).
  Smoke eval: 0 false alarms on 34 clean sentences.
- Version 0.1.13 (pyproject, __init__, description.xml, browser manifest, uv.lock).

## 2026-11-08: TYPO_DATE_FORMAT (v0.1.14)

- New rule TYPO_DATE_FORMAT (warning): ISO date `2025-12-24` -> `24.12.2025`
  and slash date `24/12/2025` -> `24.12.2025`. Source: ohjepankki
  "Ajanilmaukset: päiväys ja vuosiluku" (read 2026-11-08): Finnish uses the
  ascending dotted date; ISO is standard but not recommended in Finnish text,
  slashes are a foreign convention.
- Slash dates: automatic replacement only when the order is unambiguous
  (one group > 12); `3/4/2025` is flagged without a replacement.
  ISO dates run on the whole text (libvoikko splits at "12:") and skip
  timestamps ("2025-04-03 12:30").
- Precision: wiki sweep (24 articles, ~80k words): 2 hits, both ISO
  access-dates in citations ("Viitattu 2024-05-06") - the ohjepankki form
  would be dotted, but references are a borderline register. Smoke eval:
  0 false alarms / 34 clean sentences.
- Version 0.1.14. Stacked on the TYPO_RANGE_HYPHEN PR (v0.1.13).

## 2026-11-08: TYPO_RANGE_HYPHEN guard fixes after #35/#36 review rounds (v0.1.15)

- Equation guards (Devin rounds): pairs inside arithmetic are skipped both
  sides ("2-1=1", "1=2-1", "2-1=x", "1+(2-1)"); assignments and explanations
  still flagged ("Ikä=20-30 vuotta", "Tulos 2-1 = kotijoukkueen voitto").
- Identifier guard: prev labels starting with issn/isbn/ismn/doi skip only
  4+4-digit identifier-shaped pairs; small ranges after inflected labels
  ("ISBN-numeron 5-8 merkkiä") are flagged.
- Regression tests for all cited cases. Version 0.1.15.

## 2026-11-08: TYPO_RANGE_HYPHEN equation guard - variable operands (v0.1.16)

- Devin finding on merged #37: "2-1=x+y" and "2-1=x²" got false range
  suggestions. Equation-RHS variable token now allows single-letter
  variable operands after operators and trailing superscript exponents.
- Prose labels still flagged ("kotijoukkueen voitto", "A-joukkueen",
  "U17-joukkueen", "A/B-testin tulos").
- Regression tests for x+y and x² plus all prior cited cases. Full suite
  213 passed (2 LO sandbox deselects); smoke eval 0 false alarms / 34
  clean. Version 0.1.16.
