# TODO

- Suorituskyky: `punakyna/pipeline.py` `_spelling_suggestions` ja span-seuranta optimoitu (`_DIGITS.isdisjoint(w)` korvasi generaattorin `any(c.isdigit()...)`, `tok.lower` korvasi toistuvan `w.lower()`-kutsun, ja `startswith` korvasi toistuvat `text.find()`-haut; monikappaletekstin latenssi -42,5 %).
- Suorituskyky: `punakyna/pipeline.py` token-luonti optimoitu käyttämään `_PipelineToken`-slots-luokkaa dynaamisen `type('T', (), ...)` luomisen sijaan (kappaletarkistuksen latenssi -58 %, savutestin kokonaisaika -29 %).
- Suorituskyky: `punakyna/rules.py` `check_olla_agreement` optimoitu varhaisella poistumisella `_OLLA_3RD_PRES`-joukon ("on", "ovat") avulla välttäen turhat `_analyze`-morfologiakutsut muille sanoille (sääntökohtainen suoritusnopeutus ~79 %).
- Suorituskyky: `punakyna/rules.py` `check_double_word` optimoitu varhaisella poistumisella `prev.lower != cur.lower` välttäen turhat virkekatkelmien osamerkkijonoviipaloinnit, `.strip()`-operaatiot ja `isupper()`-tarkistukset peräkkäisille erillisille sanoille (sääntökohtainen suoritusnopeutus ~61,7 %).
- Suorituskyky: `punakyna/rules.py` `check_attribute_agreement` optimoitu varhaisella poistumisella `if not a_num: continue` ensimmäisen sanan adjektiivitarkistuksen jälkeen välttäen toisen sanan tarpeettomat `_analyze`- ja `_only_noun_number`-kutsut (sääntökohtainen suoritusnopeutus ~26,7 %, koko oikolukuputken latenssi -6,6 %).
- Suorituskyky: `punakyna/rules.py` `check_typography` optimoitu nopeilla merkkisisältötarkistuksilla (`in`) ennen regex-hakuja `%`, `€/$ /£`, `.` ja `-` (sääntökohtainen suoritusnopeutus ~64,0 %, koko oikolukuputken latenssi -11,3 %).
- v0.1 (2026-11-03): initial pipeline, 7 unit tests passing, smoke eval
  19 error / 20 clean sentences, 0 false alarms.
- v0.2 (2026-11-03): VOIKKO_GC-taso lisätty (ctypes-kaare, pip-sidonnan
  grammarErrors-bugin kierto, verifioitu upstream-korjepaketilla 66/68),
  SENT_START_CASE korvattu Voikon omalla tarkistuksella, CAP_COMMON_NOUN
  tarkennettu (erisnimivaraus, style-taso), 13 yksikkotestia, savutesti
  25 virhe- / 28 puhdasta lausetta, 0 vaaraa halytysta. Katso README.
- Open: repo home decision (where does this live), then CI (GitHub Actions:
  pytest + eval, build libvoikko from source in workflow).
- Open: FinnGEC authors to be asked about weight/data licensing.
- v0.3 (2026-11-03): held-out eval DaLA Finnish correction/test (n=10000
  paria); omat saannot tarkennettu loydettyjen FP-luokkien osalta
  (ks. README "Erillinen arviointi"); 14 yksikkotestia.
- Open: VOIKKO_GC-koodit 8/15/17/18 eivat ole viestikartassa (info-taso,
  yleisviesti) — selvitettava libvoikkolahteista.
- Open: SPELL liputtaa latinankieliset lajinimet ja vieraskieliset nimet
  (sanastokattavuus); harkittava vieraskielten tunnistusta tai
  kayttajakohtaista sanastoa.
- Open: FinnGEC-testijakoa ei ole julkisesti; DaLA-fi on synteettinen
  valitys. Aidon puhujan validoima aineisto puuttuu edelleen.

## Kehitysjono (TDT-löydökset 2026-11-03, ei viritetty)

- NEG_CONNEGATIVE: puhekielen "et" (=että) jäsentyy kieltoverbiksi ->
  vääriä osumia etta-sivulauseissa. Harkinta: älä liputa, jos "kieltoverbin"
  jälkeen seuraa pronominisubjekti (mä/sä/se/ne) + ei 2.pers. verbi.
- NEG_CONNEGATIVE: verbiketjut ("ei voisi maksaa") - hyväksy konditionaali/
  modaalikonnegatiivi ensimmäisenä ja pysähdytä.
- SV_AGREEMENT: eksistentiaalilauseen partitiivimonikon subjekti on oikein
  yksiköllisen verbin kanssa; sääntö parittaa joskus väärän subjektin.
  Vaatii joko tarkemman jäsennyksen tai parsituen (Turku parser -taso).
- DOUBLE_WORD: interjektiotoisto ("hip hip hurraa") - harkitse style-tasoa
  tai tunnettujen interjektioiden varausta.

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

## 2026-11-05: Mac bundled-package crash

- Fix staged dylib signing order and reject stale signatures in final OXT.
- Added cross-platform page-hash regressions; real Mac host harness added.
- Pending: run codesign on macOS, produce the replacement only when build
  costs are cleared, run the actual LibreOffice Mac host/GUI gates, and verify
  correction application. Existing shipped OXT is a failed build, not ready.

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

- Kovennus: `_validate_app_name` `punakyna/tokenfile.py`:ssa muutettu
  sallijalistapohjaiseksi (`^[a-zA-Z0-9](?:[a-zA-Z0-9_\-\.]{0,62}[a-zA-Z0-9])?$`).
  Torjuu ohjausmerkit (CRLF), piilotiedostot, välimerkit ja liian pitkät tunnisteet.
- Testit: `tests/test_api_hardening.py` laajennettu kattamaan sallijalistan
  rajatapaukset (134 yksikkötestiä hyväksytty).
- Seuraavaksi: sovellusten oikeuksien hienojakoisempi rajaus ja audit-loki.

## 2026-11-05: Host header validation hardening (Sentinel)

- Kovennus: `_valid_host_header` `punakyna/api.py`:ssa tarkistaa loopback-isännän
  ja portin numeerisuuden sekä arvoalueen (1-65535). Sallii oikein `[::1]` ja `::1`
  ilman porttia sekä torjuu `127.0.0.1:evil` kaltaiset vääristymät.
- Testit: `tests/test_api_hardening.py` päivitetty kattamaan rajatapaukset.

## 2026-11-07: Security response headers enhancement (Sentinel)

- Parannus: lisätty `X-Content-Type-Options: nosniff` ja `X-Frame-Options: DENY`
  HTTP-palvelimen vastauksiin (`punakyna/api.py`).
- Torjuu MIME-tyypin nuuskimisen ja selaimen kehysupotuksen / clickjacking-riskit.
- Testit: `tests/test_api_hardening.py` päivitetty kattamaan turvaotsakkeet.

## 2026-11-08: Fallback error handling & server banner hardening (Sentinel)

- Kovennus: `send_error` ylikirjoitettu `punakyna/api.py`:ssa palauttamaan JSON-virheviesti
  turvaotsakkeilla (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`) oletus-HTML-virhesivujen sijasta.
- Kovennus: `version_string` ylikirjoitettu palauttamaan vain `Punakyna/0.5` ilman alustan
  tai Python-version paljastamista `Server`-otsakkeessa.
- Testit: `tests/test_api_hardening.py` laajennettu käsittelemättömien metodien ja bannerin testauksella.

## 2026-11-09: Token loading application identifier validation (Sentinel)

- Kovennus: `load_all_tokens` `punakyna/tokenfile.py`:ssa validoi tiedostonimet
  kutsumalla `_validate_app_name`, jolloin piilotiedostot ja epäkelvot tiedostonimet
  ohitetaan automaattisesti eivätkä toimi tunnistautumisessa.
- Testit: `tests/test_api_hardening.py` laajennettu varmistamaan epäkelpojen tiedostojen ohitus.

## 2026-11-09: Client loopback destination host validation (Sentinel)

- Kovennus: `punakyna/client.py`:n `check`-funktio validoi kohteen `host`-osoitteen
  ja sallii vain loopback-osoitteet (`127.0.0.1`, `localhost`, `::1`, `[::1]`).
  Torjuu paikallisen Bearer-tunnuksen ja dokumenttitekstin vuotamisen ulkoverkkoon.
- Testit: `tests/test_client.py` päivitetty kattamaan ei-loopback-osoitteiden hylkäämisen.
- v0.1.1 (2026-11-07): PERFECT_PASSIVE_PARTICIPLE-saanto ("olen menty" -> "olen mennyt"; VISK §1292, §530). Katso AGENTS.md.
- v0.1.2 (2026-11-07): sääntörekisteri + kattavuuskartta (docs/coverage-map.md); ei toiminnallisia muutoksia.

- LibreOffice update feed (2026-11-07): description.xml update-information, make_update_xml.py, update-feed.yml; first real check needs a published full release. Version 0.1.3.
- v0.1.4 (2026-11-07): SV_NUMBER_NONOLLA (yksikkösubjekti + monikkoverbi), PERFECT_PASSIVE_PARTICIPLE-taulukko laajennettu ja testattu Voikkoa vasten. Katso AGENTS.md.
- v0.1.5 (2026-11-07): NUM_NOUN_CASE (kolme lapsi -> kolme lasta; VISK §789, §773). Katso AGENTS.md.
- v0.1.6 (2026-11-07): STYLE_SENTENCE_LENGTH + --profile virkakieli (opt-in). Katso docs/style-advice.md, AGENTS.md.
- v0.1.7 (2026-11-07): ATTR_AGREEMENT (isot talo -> isot talot; VISK §1302, §582). Katso AGENTS.md.
- v0.1.8 (2026-11-07): TYPO_PERCENT_SPACE, TYPO_CURRENCY_SPACE, TYPO_CLOCK_FORMAT, TYPO_ABBR_DOT (ohjepankki). Katso docs/ohjepankki-candidates.md, AGENTS.md.
- v0.1.9 (2026-11-08): API: virhevastaus sulkee yhteyden, HEAD ilman runkoa (#29:n katselmoinnin korjaukset). Katso AGENTS.md.
- v0.1.10 (2026-11-08): TYPO_DECIMAL_POINT (ohjepankki, desimaaliluvut). Seuraavaksi: ajatusviiva lukuvälillä (20-30 -> 20–30), päivämäärät.
- v0.1.11 (2026-11-08): opt-in debug-loki ja virhetyyppikokeilu LibreOffice-adapteriin (smear-vika Spelling-dialogissa). Oletus ei muutu.
- v0.1.12 (2026-11-08): update-feed siirretty kiinteään update-feed-julkaisuun (releases/latest ei toimi luonnos-/esijulkaisuille).

- v0.1.13 (2026-11-08): TYPO_RANGE_HYPHEN (ohjepankki, ajatusviiva rajakohdissa). Seuraavaksi: päivämäärämuodot (12/5/2025, ISO 2025-12-24). Katso AGENTS.md.

- v0.1.14 (2026-11-08): TYPO_DATE_FORMAT (ohjepankki, päiväys pistein; ISO ja kauttaviiva liputetaan). Seuraavaksi: numeroiden ryhmittely, ss./vv. Katso AGENTS.md.

- v0.1.15 (2026-11-08): TYPO_RANGE_HYPHEN-tarkistusten tarkennukset (yhtälöt, ISSN-tunnukset). Katso AGENTS.md.

- v0.1.16 (2026-11-08): yhtälösuoja sallii muuttujatermit (x+y) ja yläindeksieksponentit (x²). Katso AGENTS.md.
