# Punakynä - kyky- ja tila­matriisi

Päivitetty 2026-11-03, HEAD e6a4584+. Testitila: 98/98 läpi (Linux-sandbox).
Natiivi Mac-savutesti (CLI, Apple Silicon, brew libvoikko 4.3.3 + voikko-fi 2.5):
DOUBLE_WORD ja NEG_CONNEGATIVE liputtu oikein 2026-11-03. Editori-
integraatiot ja laajempi tarkkuus Macilla edelleen testaamatta.
"Todennettu" = automaattitesti ajaa todellisen ketjun, ei mallia.

## Pinta-alueittain

| Komponentti | Tila | Näyttö |
|---|---|---|
| Moottorin ydin (Voikko GC ctypes + omat säännöt) | Todennettu | pytest; libvoikko-ketju, rinnakkaisuuslukko (ei-säieturvallinen libvoikko) |
| Säännöt (DOUBLE_WORD, negation kongruenssi, passiivi, VISK §1581 -korjaus) | Todennettu | TDT-dev-lippuaste 0,51 %, jäädytetyt säännöt |
| Paikallinen API (8377) | Todennettu | Bearer-auth, Host/Origin-tarkistus, 1MB/200k-rajat, 30s-lukuaikakatkaisu, yhteyskatto (503 ilman säikeen luontia), ~244 req/s (Linux, EI Mac-mitta) |
| Sovellustunnukset (enrollment) | Todennettu | --enroll-app/--revoke-app/--list-apps; peruutus voimassa ilman uudelleenkäynnistystä (401 testattu); tyhjä tunnusjoukko evää aina |
| CLI | Todennettu | pytest |
| LO-UNO-skripti (korostus + palautus) | Todennettu | Todellinen headless LO 7.3: kappalelistaus, tarkistus, aalto alleviivaus, alkuperäisten palautus, muokkaustunnistus |
| LO XProofreader (.oxt) | Todennettu | Headless E2E: unopkg-asennus kertakäyttöprofiiliin, rekisteröinti LinguServiceManageriin, doProofreading, DOUBLE_WORD-sijainnit, emoji->UTF-16-siirtymä (10->11), puhdas virke |
| Selain: native messaging + laajennos | Todennettu (kehitystaso) | Firefox ESR headless E2E: laajennos -> isäntä -> API -> DOUBLE_WORD takaisin; sovellustunnus 'firefox-e2e'; ympäristö palautetaan testissä |
| Johdotusrajapinnan sijaintikäytäntö | Lukittu | Kaikki pinnat Python-koodipisteet; sovittimet muuntavat (offsets.py); testit emoji + yhdistävät merkit |

## Kehitystason rajat (eivät julkaisuvalmiita)

- Selaintesti: väliaikaisprofiili + xpinstall.signatures.required=false.
  Julkaisu vaatii allekirjoitetun laajennospaketin ja pysyvän
  isäntämanifestin asennuksen - ei toteutettu.
- Brändätty Google Chrome ohittaa --load-extension:in; automaatiotesti
  vain Firefoxilla. Laajennos itse on selainriippumaton MV2-luonnos.
- XProofreader testattu vain headless-reitillä; Writerin interaktiivinen
  oikoluku-UI (sininen aaltoviiva, ignore-rule -valikko) testaamatta
  graafisessa istunnossa.

## Ei aloitettu / vaatii alustan

- macOS NSSpellServer (.service): LUONNOS, kääntämätön ja testaamaton
  (adapters/macos/Punakyna.service/). Vaatii Macin + Xcoden.
- Trankit (TurkuNLP:n suosittelema jäsennin): sandboxin RAM ei riitä
  (xlm-roberta-base > 1,75 GB). Mittaamaton paikka - EI uusia OOM-yrityksiä.
- Parser-tason (Stanza fin_tdt, opt-in, oletus POIS) laatumittaukset ovat
  koekoodin a70b7fd mittauksia, EI moottoripolun validointia.

## Lisenssirajat

- Stanza-malleja EI paketoida eikä ladata automaattisesti
  (download_method=None): ODC-BY 1.0 + UD_Finnish-TDT CC BY-SA 4.0,
  Stanford itsessään merkitsee jakelulisenssin epäselväksi.
  Paikallinen tutkimuskäyttö oletus, ei oikeudellinen varmuus.

## Aidot Mac-validointiaskeleet (kun Mac saatavilla)

1. `brew install libvoikko voikko-fi`; ympäristömuuttujat vastaaviin
   polkuihin; aja koko pytest-patteristo.
2. Mittaa API-latenssi Mac-laitteistolla (Linux-luku ei päde). CLI-savutesti
   on jo tehty Macilla (yllä); API/testipatteristo Macilla vielä ajamatta.
3. Käännä Punakyna.service Xcodella, allekirjoita, asenna
   ~/Library/Services/ -hakemistoon; todenna NSSpellServer-rekisteröinti
   ja checkGrammar-polku; DirtyDict-mitigoinnit (ei polkujen tulkintaa).
4. Asenna .oxt Macin LibreOfficeen; graafinen oikoluku-UI -testi.
5. Trankit Macilla (RAM > 4 GB); laatu- ja suorituskykyvertailu
   Stanza-tasoa vastaan.
6. Allekirjoitettu selainlaajennos + pysyvä manifesti aidolla profiililla.

## Repo-valmius

Paikallinen repo, ei remotea, siisti puu, 94/94 testiä. Kun käyttäjä
luo yksityisen `punakyna`-repon: tyhjä -> bootstrap-issue; README-alustettu
-> feature-haara + PR. Ei suoria main-puskuja, ihminen mergetsee aina.
