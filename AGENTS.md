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
- Bolt (2026-11-10): Suorituskykyoptimointi tehty `punakyna/rules.py`:ssa säännölle `check_active_perfect_passive_participle` (varhainen poistuminen TU/TY-pääteportilla ennen `_analyze`- ja `_passive_only_participle_verb`-kutsuja; portti irrottaa ensin mahdollisen liitepartikkelin `_split_tu_clitic`-apufunktiolla, jotta "mentykin"-muodot eivät karkaa tarkistukselta. Mitattu sääntökohtainen suoritusnopeutus ~77,5 % on alkuperäisestä suorasta pääteportista; liitteiden irrotuksen vaikutusta ei ole mitattu).
- Precision first: a new rule must not add false alarms on eval/smoke_clean.jsonl.
  If a rule cannot be made clean-set-safe, leave it out or mark it severity=info.
- Finnish user-facing strings are checked against Kielitoimiston sanakirja
  (kielitoimistonsanakirja.fi); do not invent "corrections" without a source.
- Do not add third-party model weights or datasets to the repo. License
  status of FinnGEC weights/data is unresolved; see README section Neurotaso.

## 2026-11-25: PUNCT_COMMA_TITLES (v0.1.25, stacked on #56)

- Uusi warning-saanto: kahden perusmuotoisen tittelin valiin tulee pilkku
  ennen nimea ("toimitusjohtaja, ekonomi Liisa Jarvinen"). Lahde:
  ohjepankki "Pilkku titteleiden valissa" (luettu 2026-11-25).
- FP-suojat: ohjeen valinnaisuustapaus (ensimmaisella tittelilla oma
  määrite, esim. "Laitoksen johtaja tohtori") ohitetaan edeltavan
  omanto-sanan tunnistuksella; vaaditaan nimi (iso alkukirjain) titteliparin
  jalkeen; FT-tyyppiset lyhennetittelit kelpaavat.
- Skippattu: pilkku-maaritteiden-valissa (pilkku muuttaa merkitysta,
  molemmat vaihtoehdot oikein -> ei deterministista saantoa; dokumentoitu).
- Tarkkuus: fi.wikipedia ~21k sanaa: 0 osumaa puhtaassa aineistossa;
  sensitivisyys ohjepankin esimerkeilla. Savutesti 0 vaaraa / 41;
  177 testia lapi; ruff F puhdas.
- Versio 0.1.25. Stacked PR:n #56 (typo-quote-mark) paalle.

## 2026-11-25: TYPO_QUOTE_MARK (v0.1.24, stacked on #55)

- Uusi warning-saanto: suorat ASCII-lainausmerkit (") suomenkielisessa
  tekstissa -> kaarevat ”. Lahteet: ohjepankki "Lainausmerkit" ja
  "Lainausmerkit ja vuorosanaviiva" (luetut 2026-11-25).
- FP-suoja: numeron vieressa oleva merkki ohitetaan (tuumamerkki).
- Tarkkuus: fi.wikipedia ~21k sanaa: 22 osumaa, kaikki tosia
  (suoria lainausmerkkeja proosassa). Savutesti 0 vaaraa / 41;
  173 testia lapi; ruff F puhdas.
- Vuorosanaviiva-osuus jai toteuttamatta: rivinalun tunnistus vaatii
  rivikontekstia, jota virkepiiri ei valita (dokumentoitu candidates.md).
- Versio 0.1.24. Stacked PR:n #55 (comma-indirect-question) paalle.

## 2026-11-25: PUNCT_COMMA_INDIRECT_QUESTION (v0.1.23, stacked on #54)

- Uusi warning-saanto: epasuora kysymyslause erotetaan paalauseesta
  pilkulla ("En tieda, missa han asuu"). Lahde: ohjepankki "Pilkku ja
  epasuora kysymyslause" (luettu 2026-11-25).
- Rajaus tarkkuuden vuoksi: vain selkein tapaus - matriisiverbi
  (kysya/tietaa/arvata/... n. 30 lemmaa) + suoraan perassa kysymyssana
  tai -ko/-ko-verbi, ilman valissa olevaa pilkkua. "siita kuka" -tyyppiset
  valisanatapaukset jaavat tunnistamatta (recall, ei FP-riskia).
- Tarkkuus: fi.wikipedia ~21k sanaa: 0 osumaa puhtaassa aineistossa;
  sensitivisyys ohjepankin esimerkeilla (5 testia). Savutesti 0 vaaraa
  / 41; 169 testia lapi; ruff F puhdas.
- Versio 0.1.23. Stacked PR:n #54 (comma-list-ja) paalle.

## 2026-11-25: PUNCT_COMMA_LIST_JA (v0.1.22, stacked on #53)

- Uusi warning-saanto: luettelon viimeisen osan ja-/seka-/tai-sanan edessa
  ei pilkkua ("Kivea, Saarikoskea, Kilpea, Hassista ja muita").
  Lahde: ohjepankki "Pilkku rinnasteisten lauseenjasenten ja luettelon
  osien valissa" (luettu 2026-11-25).
- Rajaus tarkkuuden vuoksi: liputetaan vain >= 3 osan nimiluettelot;
  ohitetaan kun edellisen pilkun ja konjunktion valissa on aarellisverbi
  (lauseketju), kun valissa on kuten-tarkennus (pilkku sulkee tarkennuksen),
  tai kun konjunktion jalkeen tulee aarellisverbi (kokonainen lause, esim.
  eksistentiaali "ja silla oli oma hallinto").
- Tarkkuus: fi.wikipedia ~21k sanaa: 5 osumaa ennen suojia (4 vaaraa) ->
  1 osuma suojien jalkeen, tosi ("...Atlantilta, seka arktinen, kuiva
  pakkassaa pohjoisesta"). Savutesti 0 vaaraa / 41; 163 testia lapi;
  ruff F puhdas.
- Versio 0.1.22. Stacked PR:n #53 (comma-lauseenvastike) paalle.

## 2026-11-25: PUNCT_COMMA_LAUSEENVASTIKE (v0.1.21)

- Uusi warning-saanto: lauseenvastiketta eika ilman-/tekemalla-rakennetta
  eroteta muusta lauseesta pilkulla. Lahde: ohjepankki "Pilkku ja
  lauseenvastike: auringon noustua lahdimme" (luettu 2026-11-25).
- Tunnistus: E-/A-infinitiivi + possessiivi (soitettuaan, voidaksemme),
  ma-infinitiivin adessiivi (tekemalla), omanto-alkuinen ajanvastike
  (auringon noustua, Suomen kesän ollessa) ja ilman-rakenne; seka pilkku
  vastikkeen jalkeen etta ennen loppuvastiketta.
- FP-suojat: konjunktiota seuraava pilkku sallittu (etta-sivulause
  vastikkeen jalkeen, ja-alkuinen paalause); "ilman muuta" -idiomi;
  monitulkintaiset infinitiivi/passiivimuodot (vastata) ohitetaan
  aarellisverbin tunnistuksessa; duplikaattisuojaus R1/R3-valilla.
- Tarkkuus: fi.wikipedia ~21k sanaa: 0 osumaa puhtaassa aineistossa;
  sensitivisyys 9 yksikkotestilla (ohjepankin omat esimerkit).
  Savutesti 0 vaaraa / 41 puhdasta; 157 testia lapi; ruff F puhdas.
- Versio 0.1.21.

## 2026-11-25: PUNCT_COMMA_RINNASTUS + _KUIN + _JOHTOLAUSE (v0.1.20, stacked on #51)

- Kolme pilkkusaantoa ohjepankista (kaikki warning):
  - PUNCT_COMMA_RINNASTUS: puuttuva pilkku kahden kokonaisen paalauseen
    valissa (ja/tai/silla + nominatiivisubjekti + aktiivinen 3. pers.
    verbi). Lahde: ohjepankki "Pilkku paalauseiden valissa".
  - PUNCT_COMMA_KUIN: liallinen pilkku suoraan kuin-sanan edella.
    Lahde: ohjepankki "Pilkku kuin-ilmauksissa".
  - PUNCT_COMMA_JOHTOLAUSE: puuttuva pilkku lainauksen ja johtolauseen
    valissa (”...” ministeri vastasi). Lahde: ohjepankki "Pilkku
    lainauksen ja johtolauseen jaljessa".
- FP-suojat (RINNASTUS): ohjepankin valinnaisuudet (1./2. persoonan ja
  passiivin verbit, hyvin lyhyet lauseet i<3); luettelosubjekti
  ("maanviljely ja karjanhoito yleistyivat" = nominatiivi + monikko-
  verbi); ripustettu yhdyssana ("Etela- ja lounais-"); analysoimaton
  sana; konjunktioparit; sillan adessiivikaytto ("silla kynalla").
- FP-suojat (KUIN): vain suoraan edeltava pilkku; edeltavat
  ikaan/ennen/toisin/samoin/aivan/niin (valinnainen tauottava pilkku).
- FP-suojat (JOHTOLAUSE): lainaus paattyy ?/!/…/... -> ei pilkkua /
  valinnainen; tunnistus rajattu yleisimpiin johtoverbeihin +
  mahdolliseen subjektiin.
- Tarkkuus: fi.wikipedia ~21k sanaa: 23 osumaa ennen suojia (13 FP) ->
  10 osumaa, kaikki tosia. KUIN- ja JOHTOLAUSE-saannoilla 0 osumaa
  puhtaassa aineistossa (sensitivisyys varmistettu yksikkotesteilla).
  Savutesti 0 vaaraa halytysta / 41 puhdasta; 145 testia lapi; ruff F puhdas.
- Versio 0.1.20. Stacked PR:n #51 (comma-subord-relative) paalle.

## 2026-11-25: PUNCT_COMMA_SUBORD + PUNCT_COMMA_RELATIVE (v0.1.19)

- Kaksi uutta pilkkusaantoa ohjepankista (molemmat warning):
  - PUNCT_COMMA_SUBORD: puuttuva pilkku ennen alistuskonjunktiota (etta,
    jotta, koska, kun, kunnes, jos, vaikka, jollei, ellei, kunhan, mikali,
    joskin). Lahde: ohjepankki "Pilkku ja alistuskonjunktiolla (esim. etta,
    jos) alkava lause" (luettu 2026-11-25).
  - PUNCT_COMMA_RELATIVE: puuttuva pilkku ennen joka/mika-relativiivia
    taivutusmuotoineen. Lahde: ohjepankki "Pilkku ja joka-, mika-
    relatiivilause" (luettu 2026-11-25). jolloin/joten/milloin/miten-
    muodot rajattu pois (kysymys- ja konnektorimerkitykset).
- Overlappi tarkistettu: libvoikko GC ei liputa puuttuvaa pilkkua ennen
  ettaa lainkaan; joka-tapauksiin koodi 18 antaa vain yleisviestin
  (style-taso), oma saanto antaa tarkan viestin ja korjausehdotuksen.
- FP-suojat (SUBORD): virkkeen alku; yhden sanan paalause (pilkku
  valinnainen, "Toivon etta tulet"); konjunktioparit ("tai jos",
  "mutta vaikka", "etta kun"); korostussanat (etenkin, varsinkin,
  erityisesti, nimenomaan, juuri, vasta, heti, myos, paitsi - pilkku voi
  olla sanan edella); korrelaatti "seka ... etta"; idioomit "mita/enta
  jos"; raja-merkki tai pilkku jo valissa; isolla alkava muoto kesken
  virkkeen (erisnimi tai otsikon jalkeinen virkkeen alku).
- FP-suojat (RELATIVE): virkkeen alku; pilkku/raja-merkki valissa;
  konjunktioparit ("ja/tai/etta joka"); yleispronominit "mika/mita/mihin
  tahansa (hyvansa)"; "joka/mika" vain kun seuraava sana ei analysoidu
  nominiksi ("joka paiva" jaa pois - tarkkuusrajoitus: "auto joka mies
  osti" jaa liputtamatta); isolla alkava (esim. yritysnimi Jolla).
- Tarkkuus: fi.wikipedia-aineisto 5 artikkelia (~21k sanaa, haettu
  web-fetchilla koska wikimedia rajoitti sweep-IP:ta): 6 osumaa, 5 tosia
  + 1 raja-tapaus (sääntökirjan telegrafista tekstia "Tarkoitetaan jos").
  Ennen suojia 13 osumaa, joista 7 FP:tä (mika tahansa, paitsi jos, heti
  kun, myos mikali, Jolla-nimi, otsikko+Kun). Savutesti 0 vaaraa halytysta
  / 41 puhdasta lausetta; 139 yksikkotestia lapi, ruff F puhdas.
- Versio 0.1.19 (pyproject, __init__, description.xml, browser manifest,
  uv.lock).
- Seuraavaksi (ohjepankki Tier B): pilkku-paalauseiden-valissa,
  pilkku-kuin-ilmauksissa, pilkku-lainauksen-ja-johtolauseen-jaljessa
  (kaikki viela title-tasolla, sivut luettava ennen saantoa).

## 2026-11-22: PUNCT_COMMA_MUTTA_VAAN (v0.1.18, stacked on v0.1.17)

- Uusi saanto (warning): puuttuva pilkku ennen mutta/vaan-konjunktiota, kun
  sen jalkeen seuraa kokonainen paalause ("Mies tuli kotiin mutta nainen
  lahti toihin."). Lahde: ohjepankki "Pilkku ja mutta, vaan"
  (luettu 2026-11-22): kokonaiset paalauseet -> aina pilkku; jos mutta-jakso
  ei ole kokonainen paalause, pilkku on uuden saannon mukaan valinnainen.
- Tarkkuustunnistus: heti konjunktion jalkeen nominatiivinen subjekti-
  ehdokas (nimisana/asemosana/nimi, ei partisiippia) ja suoraan sen jalkeen
  finiittiverbi (tai kieltoverbi, joka kattaa "mutta kukaan ei kuunnellut").
  Ohitetaan: pilkku jo paikallaan, konjunktiota suoraan seuraava kieltoverbi
  ("mutta eivat ginsengjuurta" = yhteinen subjekti), virkkeen alku.
- Tietoiset recall-railot: "mutta viikonloppuisin siella kay" (subjekti ei
  suoraan konjunktion jalkeen) ja muut valissa olevat sanat.
- Adverbiaali/adjektiivi-FP:t estetty vaatimalla subjekti+verbi-pari
  ("Hidas mutta varma tie vie" ei liputu).
- Tarkkuus: wiki sweep 12 artikkelia (~50k sanaa): 1 osuma, tosi
  ("...eivat sijaitse pisteessa vaan ne sijaitsevat..." - paalause vaan-sanan
  jalkeen); savutesti 0 vaaraa halytysta / 41 puhdasta lausetta. Versio 0.1.18.

## 2026-11-22: TYPO_NUMBER_GROUP + ABBR_SS_VV (v0.1.17)

- TYPO_NUMBER_GROUP (warning): numeroiden ryhmittely kolmen ryhmiin lopusta
  ("5603075" -> "5 603 075"). Lähde: ohjepankki "Luvut ja numerot: numeroiden
  ryhmittely" (luettu 2026-11-22): neli- ja useampinumeroiset ryhmitellaan;
  vuosiluvut, tunnukset, puhelin- ja postinumerot poikkeuksia.
- Rajoitettu tarkoituksella: vahintaan 5-numeroinen aina; 4-numeroinen vain
  yksikon edessa ("4000 euroa"). Ohitetaan etunollalliset (puhelinnumerot),
  10+ numeroiset (tilinumerot), tunnuskontekstit (#, =, +, *, /, (, ^, piste/
  kaksoispiste/viiva + numero), yhdyssanajatkeet ("80387-matematiikkasuoritin"),
  isokirjaimisen lyhenteen perassa ("ISO 26262") ja postinumerot
  ("33100 Tampere"). Yksikkotarkistus on aakkoskoosta riippuvainen, jottei
  "1938 MM-kisoissa" liputu (mm-yksikko vs MM-kisat).
- ABBR_SS_VV (style): "ss." -> "s.", "vv." -> "v." (vanhentuneet).
  Lahteet: ohjepankin lyhenteet-pisteelliset-sivun Tiesitko-ohje ja
  Kielikello "Vanhentunut vv." (luetut 2026-11-22). 'ss'/'vv' lisatty
  pipeline._ABBREV-joukkoon, jottei SPELL liputa kahta kertaa.
- Ryhmittely ajetaan koko tekstille (_check_numgroup, kuten kello/paivays),
  koska libvoikko katkaisee virkkeen kaksoispisteeseen ("30:12345").
- Tarkkuus: wiki sweep 24 artikkelia (~88k sanaa): 1 osuma, tosi
  ("7000 vuotta sitten"); savutesti 0 vaaraa halytysta / 38 puhdasta.
- Versio 0.1.17 (pyproject, __init__, description.xml, browser manifest, uv.lock).
- Seuraavaksi (sivussa): eaa./eKr. luettu - molemmat muodot kelpaavat
  ohjepankin mukaan, ei saantoa; pilkku + mutta/vaan -tyon alla erillisessa PR:ssa.

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
- Next: keep the loopback rejection regression tests passing when changing client destination parsing or transport.

## 2026-11-10: Connection close on invalid Content-Length (Sentinel)

- When `Content-Length` header in `punakyna/api.py` fails numeric parsing, the server now drains available input bytes, sets `self.close_connection = True`, and sends `Connection: close` with the 400 Bad Request response.
- Prevents HTTP connection desynchronization / request smuggling where unparsed body bytes poison subsequent HTTP requests on persistent connections.
- Added regression test in `tests/test_api_hardening.py`.

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

## 2026-11-12: GitHub Actions CI (ruff + pytest + savutesti)

- Uusi `.github/workflows/ci.yml`: PR- ja main-push-triggeri, ubuntu-latest,
  `permissions: contents: read`, SHA-pinatut actionit, ei artefakteja eika valimuistia.
  Vaiheet: apt (libvoikko1, voikko-fi, python3-uno, xvfb) -> uv sync --frozen
  -> ruff (F-kategoria) -> pytest tests/ -> eval/evaluate.py (informatiivinen).
- Ruff lisatty dev-riippuvuuteen ja lukittu uv.lock:iin; portti F-kategoriaan
  (pyflakes). E-tyyliluokat (E401/E402/E701/E702/E741) eivat viela portaa.
- F-korjaukset erillisessa commitissa: 28 turhaa importtia poistettu,
  3 F841-kasinkorjausta, 1 F541; `punakyna/api.py`:n TokenError-re-export
  sailytetty eksplisiittisena aliaksena (testit tuovat sen punakyna.api:sta).
- Paikallinen ajo (sandbox-Linux, libvoikko 4.3.1 + voikko-fi 2.4 deb-paketeista):
  226 passed, 6 skipped. Savutesti: 0 vaaraa halytysta / 34 puhdasta lausetta.
- CI:n ensimmainen ajo paljasti kolme ymparistovikaa, kaikki korjattu:
  (1) unopkg/soffice kaatui std::bad_alloc:iin kun PATH:in ensimmainen python
  oli virtualenvin (uv run) - LO-apuprosesseille puhdistettu LO_ENV
  (tests/test_lo_xproofreader.py, tests/test_lo_writer_gui.py); tama oli myos
  aiemmin AGENTS.md:ssa mainittu "unopkg fails in Linux sandbox" -ongelman juuri.
  (2) test_oversized_413: Python 3.12+:ssa asiakas nakee BrokenPipen kun
  palvelin hylkaa ylisuuren rungon ennen lukemista; testi hyvaksyy molemmat.
  (3) test_browser_e2e: allekirjoittamaton tilapainen laajennos latautuu vain
  Firefox ESR:ssa; CI asentaa ESR:n mozilla.org:sta.
  CI-ajo 43312317082 vihrea: 226 passed, 6 skipped, ruff siisti, eval 0 FP.
- Ei versiobumpia: CI-muutos ei muuta sovellusta eika mene OXT-pakettiin.
