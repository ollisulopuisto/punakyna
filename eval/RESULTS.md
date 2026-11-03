# Arviointitulokset ja menetelma

## Aineisto ja lisenssi

`schneiderkamplab/dala-fi-audited` (config=correction), ladattu 2026-11-03:
https://huggingface.co/datasets/schneiderkamplab/dala-fi-audited

Lisenssi (aineiston LICENSE.md, lainaus): "No blanket replacement license
is asserted. Retain per-record license, source revision, URL, title and
document attribution from provenance. DaLA selects sentences, adds task
instructions and deliberately changes recorded grammar or spelling spans;
clean controls and targets reproduce source excerpts." Tietuekohtainen
lisenssi: CC-BY-SA-3.0; GFDL (Finnish Wikipedia). Aineiston tietueita EI
tallenneta tahan repositorioon; eval-skriptit lukevat ne kayttajan
lataamasta polusta.

Rajoitteet (aineistokortin omia sanoja): synteettiset korruptiot;
automaattinen (Gemma) auditointi; "Not native-speaker validated or a gold
benchmark." Nama rajoitteet koskevat kaikkia alla olevia lukuja.

## Joukot

- **dev (kehitys, saastunut)**: testijaon 10 000 ensimmaista paria
  (seed=42). Saantoja tarkennettu taman joukon virhetarkastelulla
  2026-11-03 -> post-fix-luvut ovat "tuned/development", eivat erillista
  naytetta.
- **confirm (vahvistus, koskematon)**: testijaon parit pois lukien
  dev-parit JA parit, joiden puhdas lause esiintyy dev-joukon puhtaissa
  JA parit, joiden puhdas lause esiintyy train/validation-jakojen
  puhtaissa. Ristivuotoa havaittu: 0. Otos n=10 000 (seed=7).
  Saannot jaadytetty (v0.3); ajo tehty kerran, ei virittamista.

## Pre-fix (dev, n=10000, ennen tarkennuksia)

Puhtaiden kontrollien liputusaste (error+style): 15,70 %
(SV_AGREEMENT 30, NEG_CONNEGATIVE 19, DOUBLE_WORD 6, CAP_COMMON_NOUN 3,
VOIKKO_GC 1091, SPELL 504).

## Post-fix dev (tuned, n=10000) — ei erillinen nayte

Puhtaiden liputusaste (error+style): 15,35 %
(SV_AGREEMENT 8, NEG_CONNEGATIVE 3, DOUBLE_WORD 1, CAP_COMMON_NOUN 3,
VOIKKO_GC 1091, SPELL 504).

## Confirm (vahvistus, koskematon, n=10000 paria)

Havainto korruptoituneissa lauseissa (laucetaso, kynnyksittain):

| korruptiotyyppi | n | own | voikko (err / err+style / all) | combined (err / err+style / all) |
| --- | --- | --- | --- | --- |
| spelling | 7913 | 0,2 % | 94,0 / 94,7 / 99,9 % | 94,0 / 94,7 / 99,9 % |
| adjective_case | 800 | 0,1 % | 6,0 / 16,9 / 53,4 % | 6,1 / 17,0 / 53,5 % |
| adjective_number | 653 | 0,5 % | 4,3 / 11,2 / 46,6 % | 4,7 / 11,3 / 46,7 % |
| verb_number_agreement | 295 | 3,1 % | 2,7 / 13,9 / 54,2 % | 5,8 / 16,3 / 56,3 % |
| verb_person_agreement | 228 | 0,4 % | 4,8 / 17,5 / 53,9 % | 5,3 / 18,0 / 54,4 % |
| determiner_case | 54 | 0 % | 11,1 / 16,7 / 44,4 % | 11,1 / 16,7 / 44,4 % |
| determiner_number | 57 | 0 % | 0 / 3,5 / 49,1 % | 0 / 3,5 / 49,1 % |

Tasmallinen korjaus ehdotettuna (jokin ehdotus tuottaa span-korjauksena
tasan puhtaan lauseen): own 2/10000; voikko 7191/10000 (71,9 %);
combined 7193/10000. Voikon luku koostuu lahes kokonaan
oikeinkirjoituskorjauksista (spelling on 79 % aineistosta).

Puhtaiden kontrollilauseiden liputusaste (EIKO "vaaria korjauksia":
tyokalu ei muuta tekstia itse, kyse on liputuksesta):

| moodi | error | error+style | all (mukaan info) |
| --- | --- | --- | --- |
| own (punakynan saannot) | 0,21 % | 0,22 % | 0,22 % |
| voikko (oik. + Voikko GC) | 5,24 % | 15,07 % | 55,85 % |
| combined | 5,44 % | 15,24 % | 55,93 % |

- own-moodin 22 liputusta: SV_AGREEMENT 16, NEG_CONNEGATIVE 5,
  CAP_COMMON_NOUN 1. Naiden luokittelu (aito virhe vs. vaara halytys)
  on tekijan tarkastelu, EI riippumatonta annotointia.
- voikko/combined-moodien error-liputukset ovat kaytannossa kaikki
  SPELL-osumia (699): paaasiassa vieraskielisia nimi ja latinankielisia
  lajinimi, joita voikko-fi 2.6 ei tunne (sanastokattavuuden raja).
- error+style-liputuksen kasvu 15 %:iin tulee Voikon omasta koodista 6
  (erisnimien liitesanat), joka liputtaa tuntemattomia nimi
  (~13 % Wikipedia-lauseista); punakyna valittaa sen style-tasolla.
- all-kynnyksen 56 %: SPELL_UNKNOWN-infoilmoitukset tuntemattomista
  sanoista; eivat ole korjausehdotuksia vaan huomautuksia.

## Tulkinnan rajat

- Synteettinen Wikipedia-aineisto, yhden sanan muotokorruptiot: mittaa
  lähinnä oikeinkirjoitusta ja sanastokattavuutta. Se EI voi vahvistaa
  punakynan kielioppisaantojen havaintokykyä: niiden kohdeluokkia
  (kieltoverbin liittomuoto, nominatiivisubjektin on/ovat-kongruenssi,
  sanan toisto, aakkosellisuus) aineistossa on hyvin vahan tai ei lainkaan.
  Saantojen herkkyyden vahvistus vaatii aidon virheaineiston (FinnGEC,
  saatavuus pyynnosta).
- Aineisto ei todista ylivoimaa mistaan: punakyna kayttaa Voikkoa
  oikeinkirjoitukseen ja lisa marginaalisen maaran omia osumia
  tahan korruptioprofiiliin.
- Yhden ajokerran tulokset; otosvirhe pienimmilla luokilla (n=54-295)
  on huomattava.

## Punakynan korjaus -mitan (exact fix) rajat

- Mittari soveltaa YHDEN ehdotuksen YHDEN korjausehdotuksen yhteen
  span-kohtaan ja vertaa koko lausetta kohdelauseeseen. Useamman
  samanaikaisen virheen lause ei voi osua, vaikka yksi korjaus olisi
  oikein.
- Saannoilla, joilla ei ole korjausehdotuksia (esim. NEG_CONNEGATIVE,
  DOUBLE_WORD: pelkka viesti), exact fix on maaritelmallisesti 0 —
  luku ei mittaa naiden saantojen hyvyytta.
- VOIKKO_GC- ja SPELL-osumissa exact fix edellyttaa, etta Voikon
  ehdotuslista sisaltaa oikean muodon.

## VOIKKO_GC-virhekoodien kartoitus (2026-11-03)

Koodit 1-18 (libvoikko 4.3.3 src/grammar/error.hpp GCERR_*) on nyt
kartoitettu virallisiin suomenkielisiin viesteihin (error.cpp) ja
vakavuuksiin (punakyna/pipeline.py _GC_KIND). Puhtaalla Wikipedia-
kontrollijoukolla havaittiin myos koodeja 8 (toistuva sana), 15, 17, 18;
17/18 ovat rakenneheuristiikoita ja lipsahtavat puhtaassa tekstissa
(47/10 000), siksi style-taso. Koodi 8 havaitsee sanan toiston
(mukaan lukien punakynan savutestin molemmat tapaukset); punakynan
DOUBLE_WORD saanto on varmuusverkko, ja palleikkaiset osumat
naytetaan kerran. Koodille 8 on lisatty punakynassa nimivaraus
(toistuva iso alkukirjain lauseen sisalla, esim. "Díaz Díaz").

## Soveltuvuusrajoite (jäädytetyt tulokset)

Varmistusajon luvut kuvaavat jäädytettyä käyttäytymistä commitissa **c451f56**. Myöhemmät
commitit (9d7bc5e, 8ffa2bb) muuttivat VOIKKO_GC-koodikarttaa (koodit 8 ja 12-18), vakavuuksia,
nimisuojia ja päällekkäisyyksien deduplikointia. Jäädytetyt luvut eivät siis päde nykyiselle
HEADille sellaisenaan; uutta varmistusajoa ei tehty ohjeen mukaisesti.

## Nimi

Projekti nimettiin Punakynäksi (repo-slug `punakyna`) taman commitin yhteydessa;
aiemmat commitit ja niiden tulokset on tehty nimella "tarkka". Commit-hashit eivat muutu.

## UD_Finnish-TDT puhtaana kontrollina (2026-11-03, commit de54970-jälkeinen ajo)

Aineisto: UD_Finnish-TDT test+dev (1555+1364=2919 lausetta), lähde
https://github.com/UniversalDependencies/UD_Finnish-TDT (master), lisenssi
CC BY-SA 4.0, provenienssi: Turku Dependency Treebank (Ginter ym. 2013,
Turun yliopisto). Aineistoa ei tallenneta repoon. Genrejä: uutiset, wiki,
blogit, kaunokirjallisuus, oikeustekstit, kielioppiesimerkkejä.
Liputusaste (EI tarkkuus); osumaluokittelu alla on tekijän tarkastelua,
ei riippumatonta annotointia.

- omat säännöt, error-taso: 25/2919 (0,86 %) - Wikipedia-kontrollin 0,21 % korkeampi
- omat säännöt, error+style: 0,86 %
- voikko-gc: 366/2919 (12,5 %); hallitsevat: koodi 6 erisnimiheuristiikka (191)
  ja koodi 5 virkkeenalkuisuus (96; TDT:ssä paljon otsikkomaisia fragmentteja)
- oikeinkirjoitus (tuntematon sana): 22,0 % (nimet, puhekielen muodot)

Omien sääntöjen osumien tarkastelu (ensimmäiset ~28):
- SV_AGREEMENT: suuri osa OSUMIA ON OIKEITA normin mukaan: nom.monikko +
  yksiköllinen "on" ("Tällaiset valvontatiedot on asetettava", "Tarjoukset on
  jätettävä", "Turvavyöt on pidettävä", EU-oikeustekstit ja blogit). Osa on
  kuitenkin vääriä: eksistentiaalilauseen partitiivimonikko on oikein
  ("on julkaistu useita tutkimuksia" - sääntö paritti väärän subjektin).
  "Kuvaukset on tarkoitus aloittaa" -tyyppi ratkaisematon (kieliopillisesti
  vaihtelevaa).
- NEG_CONNEGATIVE: systemaattinen väärien osumien lähde loytyi: puhekielen
  "et" (=että) Voikko jäsentää kieltoverbiksi (2. pers. yks.), jolloin sääntö
  liputtaa etta-sivulauseen verbin ("et mä istun", "et sulla on kassi").
  Lisäksi ketjut: "ei voisi maksaa" on oikein mutta liputettiin (säännön tulisi
  hyväksyä konditionaalikonnegatiivi "voisi" ja pysähtyä). Blogitekstin
  puhekielimuodot ("riehuu" konnegatiivina?) osin ratkaisemattomia.
- DOUBLE_WORD: "hip hip hurraa", "nosta nosta" (kielioppiesimerkki) - toistoa
  on, mutta osa tarkoituksellista/interjektiota.

Sääntöjä EI viritetty näiden perusteella: aineisto muuttuisi silloin
kehitysjoukoksi. Löydökset kirjattu kehitysjonoiksi (TODO.md).

## Parsittu taso (kehittysvaiheen mittaus, 2026-11-03)

Kokeellinen Stanza fin_tdt -pohjainen hybridi (eval/parse_probe.py): jäsentin
rakennetaan, Voikko varmistaa morfologian (jäsentimen piirteet normalisoituvat
virhesyötteessä - esim. "nähnyt" tagattiin Plur). Säännöt: PSV_NUMBER,
PSV_PERSON, PSV_NECESSIVE, PNEG_CONNEG, PNEG_NUMBER. Kalibrointi vain
dev-puolikkaalla; held-puolikas ajettu kerran. MultiBLiMP-fi-puolikkaat
muuttuivat näin kehitysaineistoksi näille säännöille. EI todiste ylivoimasta.

Havainto korruptiosta (liputusaste; jäädytetyt säännöt vs parsittu taso):
| ilmiö | jako | jäädytetty | parsittu |
| SV-P (n=835/puoli) | dev | 0 % | 23,5 % |
| SV-P | held | 0 % | 22,6 % |
| SV-# (n=300/puoli) | dev | 1,5 % (koko joukko) | 17,3 % |
| SV-# | held | - | 17,0 % |

Puhtaan liputus TDT (n=2919): parsittu 1,27 % (PSV_NECESSIVE 21, PSV_NUMBER 14,
PSV_PERSON 3, PNEG_CONNEG 1) vs jäädytetyt omat säännöt 0,86 %. Osa
PSV_NECESSIVE-osumista on samaa normipohjaista luokkaa kuin sääntötason osumat
("tiedot on asetettava"); luokittelu on tekijän tarkastelua.

Latenssi: 10-13 lausetta/s yksisäikeinen Linux-hiekkalaatikko (EI Mac-todiste);
mallin lataus ~3 s. Interaktiiviseen käyttöön rajatapaus ilman optimointia.

Lisenssit: stanza-koodi Apache-2.0; fin_tdt-malli johdettu UD_Finnish-TDT:stä
(CC BY-SA 4.0) - mallin jakelu ehtoineen selvitettävä ennen paketointia.

## KORJAUS: nesessiivi- ja passiiviosumat olivat vääriä (VISK §1581)

Aiempi arvioni, jonka mukaan osa TDT:n SV_AGREEMENT-osumista olisi "oikeita
normin mukaan" ("Tällaiset valvontatiedot on asetettava", "Turvavyöt on
pidettävä", "Näyttelijät on laitettu huutamaan"), oli VIRHE. Iso suomen
kielioppi (VISK §1581, kaino.kotus.fi/visk/sisallys.php?p=1581) esittää juuri
nämä rakenteet vakiosuomen ESIMERKKEINÄ: "Turvavyöt on pidettävä kiinnitettyinä
koko lennon ajan", "Avaimet on palautettava klo 12:een mennessä".
Nesessiivirakenne ja passiivi eivät kongruoitu nominaaliargumentin luvussa.

Korjaus (commit tähän): SV_AGREEMENT ohittaa "on"-muodon, jota seuraa
passiivin VA- tai TU-partisiippi (Voikko: PARTICIPLE present_passive /
past_passive). Parser-tason PSV_NECESSIVE-sääntö poistettu kokonaan
virheellisenä. Testit: 3 VISK-esimerkkiä + 2 passiivin perfektiä + kopula-
adjektiivin säilyvyys (25/25 vihreää).

TDT dev-joukon liputusaste korjauksen jälkeen: 15/2919 (0,51 %; aiemmin 0,86 %).
Jäljellä: SV_AGREEMENT 3 (puhekieliset todennäköisesti osuvia: "kädet on auki"
-tyyppi), NEG_CONNEGATIVE 11 (et/että-tunnettu aukko), DOUBLE_WORD 4.
TDT on näiden sääntöjen kehitysjoukko.

Parser-tason luvut post-hoc PSV_NECESSIVE-poiston jälkeen (EI uusinta-ajoa,
laskennallinen vähennys): SV-P dev 23,2 % (194/835), held 22,6 % muuttumaton;
SV-# dev 17,0 %, held 17,0 %; TDT puhdas ~0,55 % (16/2919).

## API-kuormamitta (sandbox-Linux, EI Mac-viite, eval/api_load.py)

Ennen korjausta: 8 rinnakkaista asiakasta kaatoi palvelimen libvoikkon
heap-korruptioon. Korjauksen (moottorilukko) jälkeen: 1 as. p50 3,8 ms;
8 rinnak. p95 38,2 ms; 16 rinnak. p95 69,7 ms, ~244 req/s, ei kaatumista.
Teksti ~1,5 KB puhdasta suomea.

## Jäsentävä taso moottoripolussa (opt-in, 2026-11-03)

parser_tier nyt osa moottoria (check_text(use_parser=True), CLI --parser,
API-payload use_parser). OLETUS POIS - konservatiivinen baseline ei muutu.
Backend: Stanza fin_tdt (Stanford-malli, Apache-2.0-koodi; malli opetettu
TurkuNLP:n UD_Finnish-TDT-puupankilla, CC BY-SA 4.0; mallin oma
jakelulisenssi vahvistamatta). Tämä EI ole TurkuNLP:n oma pipeline:
Turku-neural-parser-pipeline arkistoitu 5/2024 (turkunlp.org), suositus
seuraajaksi Trankit + Finnish-TDT. Trankit-mittaus EPÄONNISTUI
hiekkalaatikossa: xlm-roberta-base (1,04 Gt) ylittää muistirajan
(1,75 Gt, OOM). Trankit-backend vaatii isomman koneen / Macin.
Luvut pysyvät aiemmin mitattuina (SV-P 23,2/22,6 %, SV-# 17,0 %,
TDT puhdas ~0,55 %; Linux, ei Mac-viite).

## Mittausten koodiversion-sidonnaisuus
Parser-tason luvut (SV-P 23,2/22,6 %, SV-# 17,0 %, TDT ~0,55 %) mitattiin
eval/parse_probe.py-harjoituspollulla (commit a70b7fd + PSV_NECESSIVE-poisto).
Moottoriintegraatio (d7ec49c) on sama sääntölogiikka mutta EI uudelleen-
mitattu moottoripolussa: luvut ovat probe-version mittauksia, eivät
nykyisen moottoripolun validointia. Post-hoc-laskennalliset luvut on
merkitty erikseen eikä niitä pidä tulkita uusina mittauksina.

## Mallien lisenssit (fin_tdt, 2026-11-03, alkuperäislähteet)
- Stanza-koodi: Apache 2.0 (github.com/stanfordnlp/stanza/blob/main/LICENSE).
- Stanza-kielipaketit (mallit): ODC-BY 1.0 "to the extent that The Trustees
  ... have ownership and rights"; Stanza itse: mallien lisenssitilanne
  UD-dataan nähden on "unclear" ja ohjaa tarkistamaan puupankin lisenssin
  (stanfordnlp.github.io/stanza/performance.html; vahvistus issue #956:
  "In terms of the models, they are licensed under ODC").
- UD_Finnish-TDT-data: CC BY-SA 4.0 (TurkuNLP).
- PÄÄTELMÄ (varovainen, ei oikeusneuvontaa): paikallista tutkimuskäyttöä
  jatketaan olettamuksella, että ODC-BY 1.0 / CC BY-SA 4.0 -ehdot sen
  sallivat - emme väitä lainvarmuutta. Painosten BUNDLAUS tai
  automaattilataus käyttäjän artefaktiin on kielletty kunnes jakeluasema
  on selvitetty. parser_tier käyttää download_method=None: mallia ei
  koskaan haeta hiljaa; puuttuessa selkeä suomenkielinen virhe.
