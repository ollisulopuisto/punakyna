# Roadmap

1. Held-out evaluation: resolve FinnGEC test data license/access (or build an
   independent annotated corpus of native-writer errors), then publish
   precision/recall/F0.5 and over-correction rate per category.
2. Neural backend: evaluate a licensed Finnish GEC model behind
   punakyna/neural.py; gate on over-correction rate on clean text; suggestions
   always human-reviewed. Candidates: FinnGEC models (license TBD),
   own fine-tune on licensed data (e.g. CC BY-SA Wikipedia + synthetic errors).
3. Compound-error (yhdyssanavirhe) resource: investigate licensing of
   Kotus wordlists / Nykysuomen sanakirja data; Voikko's productive
   compounding accepts "eriomainen", "suomenkieli".
4. Comma rules (että-clauses, main-clause boundary) once a truth set exists.
5. Integration targets: CLI first; possible macOS service / postilaatikko
   integration later (separate decision).
6. Ship with voikko-fi 2.6 dictionary build instructions.

## v0.4.1 (rajapinnan turvakarkaistu ennen integraatioita)

- [ ] Asiakasautentikointi: nimetty tunnus, turvallinen jakelu, ei
      autentikoimatonta pääsyä edes loopbackissa
- [x] Origin/Host-validointi (DNS-rebinding-esto), ei sallittua CORSia,
      selaimen "simple request" -muotojen hylkäys
- [ ] Pyyntö-/rinnakkaisuus-/aikarajat; testit cross-site- ja
      DNS-rebinding-saannoille; ei tekstilokia/telemetriaa

## v0.5+ (integraatiot ja aito aineisto)

- [ ] Turku TDT (UD_Finnish, CC BY-SA 4.0) puhtaana kontrolliaineistona:
      provenienssi ja lisenssi säilytetään, aineistoa ei tallenneta repoon.
- [ ] Parsittu taso (Turku neural parser, Apache 2.0): kongruenssisääntöjen
      vertailu jäädytettyä baselinea vastaan. Latenssi mitattava erikseen
      ennen käytännöllisyysväitteitä.
- [ ] FinBERT (CC BY 4.0): ehdotusten järjestäminen / hyväksyttävyysluokittelu
      (arviointi ennen käyttöönottoa).
- [ ] FinT5-small (Finnish-NLP, Apache 2.0, 260M): neuro-GEC-taso edellyttää
      opetusaineistoa (FinnGEC-pyyntö avoin / DaLA-fi synteettinen).
- [ ] macOS NSSpellServer-.service (viite: divvun/macdivvun-service)
- [ ] LibreOffice Proofreader-laajennus (UNO)
- [ ] Selainlaajennos paikallista rajapintaa vasten

## v0.5.1 - rinnakkaisuus ja tunnuksen kovennus (tehty)

- KRIITTINEN: libvoikko-instanssi ei ole säieturvallinen - 8 rinnakkaista
  asiakasta kaatoi palvelimen heap-korruptioon (glibc "corrupted size vs.
  prev_size"). Korjaus: prosessinlaajuinen moottorilukko pipeline.check_textin
  ympärillä; ThreadingHTTPServerin saikeet jonottavat lukolle.
- Kuormamitta (sandbox-Linux, EI Mac-viite): 1 asiakas p50 3,8 ms; 16
  rinnakkaista p95 69,7 ms, ~244 req/s, ei kaatumista.
- Tunnustiedosto: symlink / ei-0600-oikeudet / liian lyhyt tunnus hylätään
  (TokenError); luonti atomisesti O_EXCL + 0600; vertailu hmac.compare_digest.
- Rungon luku 30 s aikakatkaisulla; samanaikaisten tarkistusten kattava rajoitus
  (BoundedSemaphore) + request_queue_size 32.

## AVATUT TURVAAVUT (ennen kuin kolmas osapuoli "turvalliseksi" väitetään)
- Tunnustiedosto = yksi jaettu bearer-tunnus, EI sovelluskohtaista
  valtuutusta. Mikä tahansa paikallinen prosessi, joka lukee tiedoston,
  pääsee rajapintaan. Sovitusten erillinen enrollment + peruutus tekemättä.
- Selainsovitteen suunnittelupäätös: nykyinen Origin-allowlist + CORS-kielto
  rikkoo extension-fetchn. Vaihtoehdot: (a) native messaging (suositus:
  ei HTTP:tä selaimesta ollenkaan), tai (b) tarkka Origin-CORS +
  todennettu enrollment. Ei laajaa local-web-allowlistiä koskaan.
  Käyttäjä ei ole myöntänyt laajennus-/rekisteröintilupia: ei asennusta.

## LibreOffice-sovitin (prototyyppi, adapters/libreoffice/)
- punakyna_lo.py: lukee avoimen Writer-asiakirjan kappaleet UNO-sillan yli,
  tarkistaa paikallisella rajapinnalla (token-todennus), tulostaa löydökset
  kappaleindekseillä. Ei asennettu laajennos, ei .oxt-pakettia.
- Validointitaso: TODELLINEN LibreOffice 7.3 Linuxissa (headless UNO,
  testi luo asiakirjan, löytää DOUBLE_WORDin oikeasta kappaleesta).
  EI Mac-validointi. Mac:lla vaatii oman vahvistuksen.
- Tunnuskäsittely siirretty punakyna/tokenfile.py:hin (moottoriton moduuli:
  sovitin ei tarvitse libvoikkoa asiakaspäässä).

## Selain + macOS (2026-11-03)
- Selain: native messaging valittu (adapters/browser/): isäntäprosessi +
  manifest-enrollment; ei CORS/HTTP selaimesta, tunnus ei JS:ään.
  Manifestia ei rekisteröidä ilman käyttäjän hyväksyntää; laajennos
  rakentamatta.
- macOS: docs/macos-integration.md. VoikkoSpellService kattaa jo suomen
  oikeinkirjoituksen (brew cask) - Punakynän arvo = kielioppi. Suunnitelma:
  NSSpellServer .service, delegate -> paikallinen API. Ei toteutusta/testiä
  (ei Macia sandboxissa).

## Offset-konventio (lukittu)
Kaikki pinnat (HTTP-API, CLI --json, native messaging) raportoivat
start/end Python-koodipisteinä. Muunnokset: UNO:n UTF-16-positiot ja
kursorin koodipisteliikkuminen (adapters/libreoffice/offsets.py), macOS:n
NSRange UTF-16. Testit: tests/test_wire_offsets.py + tests/test_offsets.py.

## Sovitusten tarkat tasot (sananlasku)
- LibreOffice: punakyna_lo.py on LO-komentosarja (käyttäjä ajaa), jolla on
  todellinen UNO-luenta+korostus Linux-headlessilla testattuna. Se EI ole
  asennettu XProofreader-palvelu; natiivi kielioppipalvelu (com.sun.star
  .linguistic2.XProofreader -komponentti) on erillinen työ.
- Selain: native-isäntä testattu protokollatasolla; laajennos on
  testaamaton luonnos. Ei selain-end-to-endiä vielä.
- macOS: Swift-luonnos kääntämätön ja varmistamaton.
