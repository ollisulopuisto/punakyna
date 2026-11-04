# TODO

- Suorituskyky: `punakyna/pipeline.py` token-luonti optimoitu käyttämään `_PipelineToken`-slots-luokkaa dynaamisen `type('T', (), ...)` luomisen sijaan (kappaletarkistuksen latenssi -58 %, savutestin kokonaisaika -29 %).
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
