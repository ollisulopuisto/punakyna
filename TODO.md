# TODO

- Suorituskyky: `punakyna/pipeline.py` `_spelling_suggestions` ja span-seuranta optimoitu (`_DIGITS.isdisjoint(w)` korvasi generaattorin `any(c.isdigit()...)`, `tok.lower` korvasi toistuvan `w.lower()`-kutsun, ja `startswith` korvasi toistuvat `text.find()`-haut; monikappaletekstin latenssi -42,5 %).
- Suorituskyky: `punakyna/pipeline.py` token-luonti optimoitu käyttämään `_PipelineToken`-slots-luokkaa dynaamisen `type('T', (), ...)` luomisen sijaan (kappaletarkistuksen latenssi -58 %, savutestin kokonaisaika -29 %).
- Suorituskyky: `punakyna/rules.py` `check_olla_agreement` optimoitu varhaisella poistumisella `_OLLA_3RD_PRES`-joukon ("on", "ovat") avulla välttäen turhat `_analyze`-morfologiakutsut muille sanoille (sääntökohtainen suoritusnopeutus ~79 %).
- Suorituskyky: `punakyna/rules.py` `check_double_word` optimoitu varhaisella poistumisella `prev.lower != cur.lower` välttäen turhat virkekatkelmien osamerkkijonoviipaloinnit, `.strip()`-operaatiot ja `isupper()`-tarkistukset peräkkäisille erillisille sanoille (sääntökohtainen suoritusnopeutus ~61,7 %).
- Suorituskyky: `punakyna/rules.py` `check_attribute_agreement` optimoitu varhaisella poistumisella `if not a_num: continue` ensimmäisen sanan adjektiivitarkistuksen jälkeen välttäen toisen sanan tarpeettomat `_analyze`- ja `_only_noun_number`-kutsut (sääntökohtainen suoritusnopeutus ~26,7 %, koko oikolukuputken latenssi -6,6 %).
- Suorituskyky: `punakyna/rules.py` `check_typography` optimoitu nopeilla merkkisisältötarkistuksilla (`in`) ennen regex-hakuja `%`, `€/$ /£`, `.` ja `-` (sääntökohtainen suoritusnopeutus ~64,0 %, koko oikolukuputken latenssi -11,3 %).
- Suorituskyky: `punakyna/pipeline.py` `_spelling_suggestions` optimoitu dokumenttikohtaisella `spell_cache`-välimuistilla välttäen toistuvat `voikko.spell`-kutsut samoille sanoille tekstin sisällä (oikeinkirjoitustarkistuksen suoritusnopeutus ~60,1 %, koko oikolukuputken latenssi -11,2 %).
- Suorituskyky: `punakyna/rules.py` `check_active_perfect_passive_participle` optimoitu varhaisella TU/TY-pääteportilla, joka irrottaa ensin mahdollisen liitepartikkelin `_split_tu_clitic`-apufunktiolla ("mentykin" analysoidaan eikä ohitu), välttäen turhat `_analyze`-morfologiakutsut ei-passiivimuotoisille sanoille (mitattu sääntökohtainen suoritusnopeutus ~77,5 % koskee alkuperäistä suoraa pääteporttia; liitteiden irrotusta ei ole mitattu erikseen).
- v0.1 (2026-11-03): initial pipeline, 7 unit tests passing, smoke eval
  19 error / 20 clean sentences, 0 false alarms.
- v0.2 (2026-11-03): VOIKKO_GC-taso lisätty (ctypes-kaare, pip-sidonnan
  grammarErrors-bugin kierto, verifioitu upstream-korjepaketilla 66/68),
  SENT_START_CASE korvattu Voikon omalla tarkistuksella, CAP_COMMON_NOUN
  tarkennettu (erisnimivaraus, style-taso), 13 yksikkotestia, savutesti
  25 virhe- / 28 puhdasta lausetta, 0 vaaraa halytysta. Katso README.
- Done (2026-11-12): repo home = ollisulopuisto/punakyna; CI lisatty
  (GitHub Actions: ruff F + pytest + savutesti-eval PR:eille ja
  main-pushauksille; libvoikko ja voikko-fi apt-paketeista, ei koostetta
  lahdekoodista).
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

## 2026-11-25: PUNCT_COMMA_KUTEN (v0.1.26, stacked on #57)

- Uusi warning-saanto: verbillinen kuten-jakso erotetaan paalauseesta
  pilkulla ("Sailiot ovat huonossa kunnossa, kuten kuvasta nakykin").
  Lahde: ohjepankki "Konjunktiot: kuten" (luettu 2026-11-25).
- Rajaus: 'niin kuin' -merkityksinen verbiton jakso ("Lomaile kuten
  kuninkaalliset") ei saa pilkkua, joten liputetaan vain kun kuten-sanaa
  seuraavien 5 sanan joukossa on aarellisverbi. Sama saanto kattaa myos
  'esimerkiksi'-merkityksen ("Medialaitteet, kuten TiVo, kayttavat").
- Skipattu tietoisesti: lauseenalkuinen valitettavasti/toisaalta -sivu
  (molemmat vaihtoehdot sallittuja; dokumentoitu candidates.md).
- Tarkkuus: fi.wikipedia ~21k sanaa: 6 osumaa, kaikki tosia
  (esimerkki-kuten ilman pilkkua wikipedian proosassa). Savutesti
  0 vaaraa / 41; 180 testia lapi; ruff F puhdas.
- Versio 0.1.26. Stacked PR:n #57 (comma-titles) paalle.

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
## 2026-11-10: Connection close on invalid Content-Length (Sentinel)
- Kovennus: `punakyna/api.py`:ssa epäkelpo Content-Length sulkee yhteyden (`Connection: close`,
  `close_connection = True`) ja tyhjentää saapuneen puskurin (`_drain_available`).
  Torjuu HTTP-yhteyden desynkronisaation ja request smuggling -riskin pysyvillä yhteyksillä.
- Testit: `tests/test_api_hardening.py` laajennettu kattamaan yhteyden sulkeminen virheellisellä Content-Lengthilla.

- Next: keep the loopback rejection regression tests passing when changing client destination parsing or transport.
- v0.1.17 (2026-11-22): TYPO_NUMBER_GROUP (5603075 -> 5 603 075) ja ABBR_SS_VV
  (ss. -> s., vv. -> v.). Katso AGENTS.md. Seuraavaksi: pilkku mutta/vaan
  (kokonainen paalause seuraa), eaa./eKr. luettu eika ole saantoaineisto.
- v0.1.18 (2026-11-22): PUNCT_COMMA_MUTTA_VAAN (pilkku ennen mutta/vaan +
  kokonaista paalausetta). Katso AGENTS.md.
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
