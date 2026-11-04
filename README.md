# Punakynä — suomen kielen oikolukija

Tarkistaa suomenkielisen tekstin ja palauttaa ehdotuksia merkkisijainneilla.
Ei koskaan muuta tekstiä itse: ihminen (tai kutsuva ohjelma) päättää
korjauksista.

## Miksi

Voikko on edelleen paras vapaasti saatavilla oleva suomen oikeinkirjoituksen
tarkistin (libvoikko 4.3.3 / 2025, voikko-fi 2.6 / 2026). Sen mukana tulee
myös kieliopintarkistin, mutta sen kattavuus on kapea: se tunnistaa
tiettyjä kiinteitä sana-parivirheitä (esim. "joten kuten" → "jotenkuten"),
välimerkki- ja välilyöntivirheitä sekä erisnimien liitesanojen
aakkosellisuutta, mutta ei lainkaan kongruenssi-, kieltoverbi-,
sanan-toisto- tai yleisempiä aakkosellisuusvirheitä (mitattu 2026-11-03,
ks. `eval/` ja alla "Voikon kieliopintarkistimen kattavuus").
LanguageTool ei tue suomea lainkaan, ja Apple Intelligence Writing Tools
ei tue suomea edes iOS 27:n kielilistalla. Microsoft Editor tukee suomen
kielioppia, mutta on suljettu pilvipalvelu.

Tutkimuskenttä (FinnGEC, Vu ym. 2026, aclanthology.org/2026.bea-1.33) osoittaa,
että pienet suomeksi hienosäädetyt mallit ovat lähellä suuria pilvi-LLM:itä
kieliopin korjauksessa — ja korjaavat selvästi vähemmän liikaa
(yli-korjaus eli puhtaan tekstin rikkominen on LLM:ien pahin vika).

Punakynä yhdistää nämä: Voikon oikeinkirjoitukseen, morfologiaan ja
kapeaan kieliopintarkistukseen, tarkkoja sääntöjä niihin virheluokkiin
joita Voikko ei kata, ja kytkettävän neurotason myöhempää käyttöä varten.

## Arkkitehtuuri

1. **Voikko-taso** — oikeinkirjoitus + korjausehdotukset + morfologinen
   analyysi (libvoikko, asennettava erikseen).
2. **Voikon kieliopintarkistin** (`punakyna/voikko_gc.py`, sääntö `VOIKKO_GC`)
   — libvoikko:n oma kieliopintarkistin suoraan C-rajapinnasta ctypes:llä.
   Huom: pip-paketin `libvoikko`-sidos (4.3) on rikki tässä kohden
   (grammarErrors palauttaa haamuvirheitä tai ei mitään ja voi kaataa
   prosessin); tämä moduuli kiertää bugin. Oikea toiminta on verifioitu
   libvoikko:n omaa korjepakettia vasten: 66/68 odotettua virhettä
   toistuu tasan (tests/voikkotest/fi-x-vfst/grammar.txt, voikko-fi 2.6);
   2 puuttuu, koska loppuvälimerkin puute hyväksytään keskeneräisissä
   kappaleissa (asetus AcceptUnfinishedParagraphsInGc=1, sama periaate
   kuin LibreOffice-integraatiossa).
3. **Sääntötaso** (`punakyna/rules.py`) — kapeat, tarkkuus ensin -säännöt:
   - `DOUBLE_WORD` — sana toistuu peräkkäin
   - `NEG_CONNEGATIVE` — kieltoverbin liittomuoto ("en tienneet" → "en tiennyt",
     huom. monikossa "emme tienneet" on oikein; sääntö lukee Voikon
     FST-merkinnät `[Tk]`/`[Ll][Ru]` eikä arvaile)
   - `NEG_NUMBER` — pronomini + väärä kieltosana ("He ei" → "He eivät")
   - `SV_AGREEMENT` — nominatiivinen subjekti + on/ovat-kongruenssi
     (eksistentiaalilause "Pöydällä on kirjat" jätetään rauhaan)
   - `CAP_COMMON_NOUN` — kuukausi/viikonpäivä/vuodenaika isolla
     lauseen sisällä ("Tammikuussa" → "tammikuussa"); sanastossa
     erisnimeksi tunnistettua sanaa ei koskaan liputeta, ja osuma on
     aina style-tasoa (sanakirjapohjainen työkalu ei voi tietää
     tuntematonta sukunimeä, esim. "Hänen sukunimensä on Syksy.")
4. **Neurotaso** (`punakyna/neural.py`, oletuksena pois) — rajapinta
   sekvensis-malleille. **Mukana ei jaeta mitään mallipainoja**: FinnGEC-työn
   HF-painoilla (advu/finnish-gec-*) ei ole ilmoitettua lisenssiä ja sen
   opetusaineisto on lisenssirajoitteinen. Käyttäjä voi kytkeä itse
   hankkimansa mallin; evaluointisääntö: ennen käyttöönottoa mitattava
   yli-korjausaste puhtaalla tekstillä, ja ehdotukset esitetään aina
   ihmisen tarkistettavina.

Jos Voikon kieliopintarkistin ja sääntötason osumat osuvat samaan kohtaan,
näytetään vain tarkemmin perusteltu sääntötason osuma.

## Asennus

```sh
# libvoikko + suomen sanasto (esim. Debian: libvoikko1 + voikko-fi,
# macOS: brew install libvoikko voikko-fi,
# tai lähdekoodista voikko.puimula.org/sources.html)

# uv (suositus): luo .venv:n ja asentaa riippuvuudet
uv sync
uv run python -m punakyna --serve

# tai pelkkä pip:
pip install libvoikko pytest

export PUNAKYNA_VOIKKO_DICTIONARY_PATH=/polku/jossa/5/mor-standard   # jos ei vakiopolussa (macOS/brew: /opt/homebrew/lib/voikko)
export PUNAKYNA_LIBVOIKKO_PATH=/polku/jossa/libvoikko.so.1           # jos ei vakiopolussa (macOS/brew: /opt/homebrew/lib)
```

## Käyttö

```sh
python -m punakyna teksti.txt          # luettava tuloste
python -m punakyna --json teksti.txt   # JSON, merkkisijainnit alkuperäiseen tekstiin
cat teksti.txt | python -m punakyna
python -m pytest tests/              # yksikkötestit (13 kpl)
python eval/evaluate.py              # savutestiarviointi
```

## Valinnaiset tyylivinkit

Aktiivin suosiminen sekä kertojan (minä/me) ja lukijan puhuttelun
(sinä/te) johdonmukaisuus ovat erikseen valittavia vinkkejä, eivät
kielioppivirheitä. Oletuksena pois. LibreOfficessa asetukset löytyvät
Työkalut-valikon Lisäosat-kohdasta. [Käyttö ja rajat](docs/style-advice.md).

## Voikon kieliopintarkistimen kattavuus (mitattu 2026-11-03)

Verifioitu libvoikko:n omalla korjepaketilla (corevoikko,
tests/voikkotest/fi-x-vfst/grammar.txt) ajamalla se punakynan
`voikko_gc`-kääreen läpi, sekä erikseen `voikkogc`-komentorivityökalulla
(voikko-fi 2.6). Voikko havaitsee:

- tiettyjä kiinteitä kirjoitusasuvirheitä ("joten kuten" → "jotenkuten",
  "se on vaan" → "se on vain", "loppujen lopuksi", "mielin määrin")
- kaksoisvälilyönnit, välilyönnin ennen pilkkua, tuplapilkut ja
  tiettyjä välimerkkiyhdistelmiä
- erisnimen liitesanan ison alkukirjaimen ("Reetan Taskun" → "taskun")
- lauseen alkamisen pienellä kirjaimella
- vieraskieliset lainausmerkit ja lainausmerkki+välimerkki-yhdistelmät
- sanan toiston (koodi 8; punakynan DOUBLE_WORD on varmuuden vuoksi mukana
  ja valttaa nimitapaukset kuten "Díaz Díaz" — samat osumat näytetään kerran)
- harvinaisempia rakenteita: koodi 13 (kieltoverbi+pääverbi), 14/15
  (infiniittimuodot), 16 (virkkeen lopun sidesana), 17/18 (puuttuva /
  ylimääräinen pääverbi — heuristisia, osumia myös puhtaalla tekstillä)

Voikko EI havaitse: subjekti-predikaattikongruenssia ("pojat juoksee"),
kieltoverbin liittomuotoa ("en tienneet"), pronominin ja kieltosanan
numeroa ("he ei") eikä kuukausien yms. aakkosellisuutta ("Tammikuussa"
lauseen sisällä). (Sanan toiston Voikko havaitsee, ks. yllä.)

## Arviointi ja tulokset (savutesti, 2026-11-03)

Pieni käsin rakennettu aineisto: 25 virhelausta + 28 puhdasta lausetta.
**Tämä ei ole erillinen yleistyvyysnäyte** — se on regressiotesti.
Todellinen arviointi vaatii lisensoidun testiaineiston (esim. FinnGEC,
lisenssi ja saatavuus selvityksessä; aineiston jakelu on pyynnöstä ja
testijakoa ei saa käyttää opetukseen).

| luokka | voikko (vain oik.) | voikko-kokonaisuus | punakyna |
| --- | --- | --- | --- |
| oikeinkirjoitus (SPELL) | 2/3 | 2/3 | 2/3 |
| VOIKKO_GC (Voikon omat luokat) | 0/7 | 7/7 | 7/7 |
| DOUBLE_WORD | 0/2 | 2/2 (Voikon koodi 8) | 2/2 |
| NEG_CONNEGATIVE | 0/3 | 0/3 | 3/3 |
| NEG_NUMBER | 0/2 | 0/2 | 2/2 |
| SV_AGREEMENT | 0/4 | 0/4 | 4/4 |
| CAP_COMMON_NOUN | 0/4 | 0/4 | 4/4 |
| vääriä hälytyksiä (28 puhdasta) | 0 | 0 | 0 |

Ero Voikkoon: punakyna havaitsee savutestissä kaikki sääntöluokkiensa
virheet; Voikko-kokonaisuus ei havaitse niistä kongruenssi-,
kieltoverbi- eikä aakkosellisuusluokkia (sanan toiston se havaitsee
itsekin). Voikon omissa luokissa punakyna käyttää Voikkoa itseään. Puhtaassa joukossa yksi
dokumentoitu raja-tapaus: "Hänen sukunimensä on Syksy." tuottaa
style-tason CAP_COMMON_NOUN-osuman (sama rajoite Voikolla, ks. yllä).

## Erillinen arviointi: DaLA Finnish (2026-11-03)

Täydet luvut, joukkojen rajaaminen ja tulkinnan rajat: `eval/RESULTS.md`.

Aineisto: `schneiderkamplab/dala-fi-audited` (correction/test).
Lisenssi: source-specific (LICENSE.md), tietueet CC-BY-SA-3.0; GFDL
(Finnish Wikipedia), attribuutio säilytettävä; aineistoa ei tallenneta
tähän repositorioon. Aineistokortin mukaan: synteettiset korruptiot,
automaattinen auditointi, ei aidon puhujan validoima kultastandardi.

Menetelmä: saannot viritettiin 10 000 parin kehitysjoukolla (seed=42) —
sen post-fix-luvut ovat kehityslukuja. Vahvistusajo tehtiin koskemattomalla,
erillisellä 10 000 parin joukolla (seed=7; ristivuotoa train/validation-
jakojen kanssa ei havaittu) jaadytetyillä säännöillä, yksi ajo, ei
virittämistä.

Vahvistusajon paakohdat:
- Punakynan omien saantojen liputusaste puhtailla kontrollilauseilla:
  0,21 % (error) / 0,22 % (error+style). Huom: tama on liputusaste,
  ei tarkkuusmittari (precision) — puhtaan joukon liputukset eivat
  kerro osumien osuudesta oikeita ilman riippumatonta annotointia;
  osumien luokittelu tassa on tekijan tarkastelua.
- Oikeinkirjoituskorruptioiden havainto 94,0 % ja tasmallinen
  korjaus ehdotettuna 71,9 % — tama on Voikon suorituskykya, jonka
  punakyna kayttaa sellaisenaan.
- Aineiston kielioppikorruptiotyypit ovat suureksi osaksi punakynan
  saantojen ulkopuolella; havaintoluvut (0-6 % error-kynnyksella)
  EIVAT kerro saantojen herkkyydesta aitoihin virheisiin. Sen
  vahvistus vaatii aidon virheaineiston (FinnGEC, saatavuus pyynnosta).
- Voikon oman GC-koodin 6 erisnimiheuristiikka liputtaa ~13 %
  Wikipedia-lauseista (tuntemattomat nimet); punakyna valittaa sen
  style-tasolla, ei errorina.


## Arkkitehtuuri ja integraatiot

Punakynä on jaettu paikallinen oikolukumoottori:

1. **Ydin** (`punakyna/`-paketti): Voikko-oikeinkirjoitus + Voikon kieliopin-
   tarkistin + omat säännöt. Ei riippuvuuksia libvoikkoa lukuun ottamatta.
   Prosessinlaajuinen lukko (libvoikko ei ole säieturvallinen).
   Valinnainen neurotaso (`--parser`, oletus POIS): Stanza fin_tdt +
   Voikko-hybridi, ei koskaan automaattista mallilatausta.
2. **CLI** (`python -m punakyna`): tiedosto/stdin -> ehdotukset.
3. **Paikallinen HTTP-rajapinta** (`python -m punakyna --serve`,
   `punakyna/api.py`): vain loopback, Bearer-tunnus, sovelluskohtaiset
   tunnukset (`--enroll-app`/`--revoke-app`/`--list-apps`, peruutus
   voimassa heti ilman uudelleenkäynnistystä), Host/Origin-tarkistus,
   ei CORSia, 1 MB / 200 000 merkin rajat, 30 s lukuaikakatkaisu,
   yhteyskatto. Tekstiä ei logata eikä tallenneta.
4. **LibreOffice XProofreader** (`adapters/libreoffice/xproofreader/`):
   natiivi .oxt-lisäosa (pyuno), ohut asiakas paikalliselle API:lle;
   headless-E2E todennettu (rekisteröinti, sijainnit, UTF-16-muunnos).
   Lisäksi UNO-korostusskripti (`adapters/libreoffice/`).
5. **Selain** (`adapters/browser/`): laajennos + native messaging -isäntä;
   teksti ei koskaan selaimen HTTP:hen. Firefox ESR -E2E todennettu
   (kehitystason profiili, ks. docs/kykymatrisi.md).
6. **macOS** (`adapters/macos/Punakyna.service/`): NSSpellServer-luonnos,
   kääntämätön ja testaamaton - vaatii Macin (ks. docs/macos-integration.md
   ja docs/kykymatrisi.md).

Johdotusrajapinnan sijaintikäytäntö (lukittu): kaikki pinnat raportoivat
Python-koodipisteitä; sovittimet muuntavat (esim. LO UTF-16,
`adapters/libreoffice/offsets.py`).

Teksti pysyy paikallisena oletuksena: ei pilvivälitystä, ei keräystä,
ei automaattisia korjauksia käyttäjän tekstiin.

**Kokonaistila, kehitystason rajat ja Mac-validointiaskeleet:**
[docs/kykymatrisi.md](docs/kykymatrisi.md) - **Tutkimustausta ja
viitteet:** [docs/research.md](docs/research.md)

## Tunnetut aukot

- **Yhdyssanavirheet**: Voikko hyväksyy tuottavasti yhdistelmiä kuten
  "eriomainen" (eri+omainen) ja "suomenkieli". Oikea korjaus vaatii
  sanastoresurssin (esim. Kielitoimiston sanakirjan taivutustieto ei ole
  vapaasti lisensoitu — selvitettävä).
- Pilkkusäännöt (esim. että-konjunktion pilkku) eivät ole mukana vielä;
  reunatapaukset vaativat huolellista totuusaineistoa ennen toteutusta.
- Tuntemattomat erisnimet: sanakirjaan kuulumatonta nimeä (esim. harvinainen
  sukunimi) ei voida erottaa virheestä; CAP_COMMON_NOUN-osumat ovat siksi
  aina style-tasoa ja viesti muistuttaa nimimahdollisuudesta.
- Loppuvälimerkin puutetta ei liputeta (AcceptUnfinishedParagraphsInGc=1;
  sama periaate kuin LibreOffice-integraatiossa).
- Puhekieli: punakyna tarkistaa yleiskieltä; puhekielisiä muotoja ei
  "korjata", mutta niitä ei myöskään erityisesti hyväksytä.
- Käyttää voikko-fi 2.6 -sanastoa (2026-04).

## Lisenssit

- punakyna-koodi: MIT (ks. LICENSE).
- libvoikko: MPL 1.1 / GPL 2+ / LGPL 2.1+ (kolmilisenssi). voikko-fi: GPL 2+.
- Kolmannen osapuolen mallipainoja tai aineistoja ei jaeta tässä paketissa.

## Taustaa

- Vu ym. 2026: *FinnGEC: Benchmarking Grammatical Error Correction for
  Finnish* (BEA 2026), aclanthology.org/2026.bea-1.33 — ensimmäinen suomen
  GEC-mittaristo. Taulukko 5 (testijoukko): GPT-5.4 zero-shot P 47.27 /
  R 60.10 / F0.5 49.37 / OC 57.0; Claude Haiku 4.5 P 39.23 / R 42.31 /
  F0.5 39.81 / OC 47.9; hienosäädetty FinT5 260M P 48.17 / R 40.25 /
  F0.5 46.35 / OC 23.4; mBART 611M P 51.13 / R 22.84 / F0.5 40.98 /
  OC 9.9; Poro2 8B P 40.54 / R 43.36 / F0.5 41.07 / OC 22.6.
- Creutz 2024 (W-NUT): GPT-4 paras oppijan-tekstien korjaajana mutta
  uudelleenmuotoilee.
- Voikko: voikko.puimula.org
