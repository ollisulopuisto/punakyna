# Punakynä - tutkimustausta ja viitteet

Miksi Punakynä on rakennettu näin, ja mihin tutkimukseen ratkaisut
nojaavat. Arvioinnin numerot: `docs/kykymatrisi.md` ja alla
"Mittaukset".

## Lähtökohta: Voikon rooli

Voikko (libvoikko 4.3.3, voikko-fi-sanasto) on vakaa ja laajasti käytetty
suomen oikeinkirjoituksen tarkistin.[^voikko] Sen mukana tuleva
kieliopintarkistin on tarkoituksella konservatiivinen: se tunnistaa
lähinnä kiinteitä sanaparivirheitä, välimerkki- ja välityylejä sekä
osan rakennepuutteista (mitattu 2026-11-03, ks. README
"Voikon kieliopintarkistimen kattavuus"). Kongruenssia (subjekti-
verbi, kieltoverbi) Voikko ei tarkista. Punakynä täydentää tätä -
ei korvaa Voikkoa.

## Mitä neuroverkot tuovat - ja mitä eivät

FinnGEC-työkalurivi (Vu ym. 2026)[^finngec] osoittaa, että pienet
suomeksi hienosäädetyt mallit yltävät lähelle suuria pilvi-LLM:iä
kieliopin korjauksessa - ja ylikorjaavat vähemmän. Creutz (2024)
havaitsee vastaavasti, että LLM:t suoriutuvat vaativissakin
oppijansuomen teksteissä hyvin, mutta kyse on kokonaislauseiden
uudelleenkirjoituksesta (koeasetelma hyväksyy sujuvuuskorjaukset),
ei virheiden osoittamisesta paikkatarkasti.[^creutz] Punakynän
valinta: osoittaa virheet ja antaa ehdotuksia, ei kirjoittaa tekstiä
uudelleen - käyttäjä päättää aina.

## TurkuNLP-linja

Turun yliopiston NLP-ryhmän (TurkuNLP) työ on suomen kieliteknologian
selkäranka: Turku Dependency Treebank (TDT)[^tdt] on keskeinen
suomen jäsennysaineisto, ja UD-versiota käytetään sekä kehitys- että
arviontidatana (tässä repossa: puhtaan tekstin väärien hälytysten
mittaus). TurkuNLP:n oma neurojäsenninputki (TNPP) on poistunut
tuotantokäytöstä 5/2024; ryhmä suosittelee seuraajaksi
Trankitia.[^tnpp]

Punakynän valinnainen jäsennystaso (`--parser`, oletus POIS) käyttää
Stanzaa[^stanza] sen suomen mallilla, joka on opetettu juuri
UD_Finnish-TDT-aineistolla - kyseessä on siis TDT-derivateetti, ei
TurkuNLP:n oma jäsennin. Stanza-mallien
jakelulisenssi on epäselvä (ODC-BY 1.0 + TDT:n CC BY-SA 4.0;
Stanton huomauttaa epäselvyydestä itsekin[^stanzalic]), joten
malleja ei paketoida eikä ladata automaattisesti.

**Trankit-päätös (2026-11-03, perusteet verifioitu livelähteistä):**
TurkuNLP:n suosittelema seuraaja on Trankit + Finnish-TDT-malli
(sama TDT-opetusaineisto kuin TNPP:llä).[^tnpp] Trankit on
Apache-2.0-koodia (PyPI v1.1.2), mutta sen riippuvuusrajaus
`torch >=1.6.0, <=2.0.1`[^trankit] on ristiriidassa nykyisten
torch 2.x -pinojen kanssa (vaatisi erillisen vanhan ympäristön),
mallit ovat xlm-roberta-base-luokkaa (ev v. 1 Gt RAM, ei mahdu
hiekkalaatikon 1,75 Gt muistiin - mitattu OOM), ja mallien
autolataus + lisenssiasema on samanlainen avoin kysymys kuin
Stanzalla. Mitattua kykyeroa Stanza fi_tdt:hen nähden ei ole:
molemmat ovat TDT-opetettuja, ja Trankitin lisäominaisuudet
(monisanalausekkeiden yhteiskäsittely, NER) eivät palvele
Punakynän kongruenssitarkistuksia. Päätös: Stanza jää
jäsennysbackendiksi; Trankit-paikka jää dokumentoiduksi
vaihtoehdoksi ilman paketointia. TurkuNLP-integraation
konkreettinen sisältö on siis itse TDT-aineisto: opetusmalli,
puhdas kontrolliaineisto ja MultiBLiMP-fi:n lähde.

## Mittaukset (2026-11-03)

MultiBLiMP 1.0:n[^multiblimp] suomen minimaaliparit (kultainen
lause vs. yhdeltä piirteeltään rikottu kaksoin):

| Ilmiö | n | Sääntö+parseri: virhe havaittu | Sääntö+parseri: oikea liputettu |
|---|---|---|---|
| SV-P (subjekti-verbi persoona) | 400 | 122 (30,5 %) | 3 (0,8 %) |
| SV-# (subjekti-verbi luku) | 400 | 75 (18,8 %) | 0 (0,0 %) |
| SP-# (subjekti-partisiippi luku) | 300 | 123 (41,0 %) | 3 (1,0 %) |

SP-# on tarkemmin sanottuna perfektin partisiipin lukukongruenssi
("on osallistunut seitsemän kilpailijaa", ei *"osallistuneet") -
ei predikatiiviadjektiivia. Uusi parseritason PPERF_NUM-sääntö
nappaa yksin 102/300 (34,0 %) virheistä, 1/300 (0,3 %) oikeista.
Sitä ennen SP-#-katavuus oli 21/300 (7,0 %).

Vain parser-taso (PSV-säännöt): SV-P 59/400 (14,8 %), SV-# 56/400
(14,0 %). Vain kevyt sääntötaso: SV-P 292/1670 (17,5 %) koko
aineistosta, 0 vaaraa halytysta oikeista. Tasot taydentavat toisiaan:
sääntötaso nappaa vierekkäiset pronomini+verbi-tapaukset, parseri
etaiset subjektit.

Puhtaan yleiskielen varakontrolli: UD_Finnish-TDT dev (1364 lausetta).
Jäädytettyjen sääntöjen kokonaislippuaste 0,51 %. Kongruenssimittarin
(PSV/PNEG/PRON_VERB_AGREEMENT/SV_AGREEMENT/PRED_NUM/PPERF_NUM)
liputukset: 4/1364 (0,29 %), joista PRED_NUM 1 (puhekielinen
lause "mikä tyynyt olisi se kaikista kivoin"), PPERF_NUM 0,
PRON_VERB_AGREEMENT 0.

Predikatiivin lukukongruenssi (PRED_NUM, parseritaso, VISK
§1284[^visk1284]): monikollinen subjekti + yksiköllinen
nominatiivipredikatiivi liputetaan ("Me ollaan likainen." -> huom.;
VISK §1284 Huom.: yksipersoonaisen passiivin predikatiivi on
monikossa, ja §1284b: puhekielessäkin predikatiivi pysyy monikossa
vaikka verbi lipsuu - "Nää kriminaalit oli ääritapauksia").
Poikkeukset: numeraalisubjekti (§1285), kollektiivierisnimet
("Helsingin Sanomat on varovainen", §1284c; myös sääntötason
SV_AGREEMENT ohittaa ne nyt). Kattavuusraja rehellisesti:
MultiBLiMP-fi:ssä EI ole predikatiiviadjektiivi-ilmiötä, joten
PRED_NUM on varmistettu kohdennetuilla tapauksilla (15 testiä) +
TDT-kontrollilla (1/1364), ei suurilla minimaalipareilla.

Tulkintaohje: "virhe havaittu" on herkkyys minimaalipareissa, joissa
virhe on tiedossa - se ylittaa todellisen kayton loydosprosentin.
"Oikea liputettu" on tarkein laatuluku: kayttaja suostuu tarkistimeen
vain jos puhdas teksti jaa rauhaan.

## Avoimet tutkimuskysymykset

- SP-#:n loppuosa (~59 %) jakautuu tapauksiin, joissa parseri
  normalisoi virheellisen lauseen piirteet tai subjektin tunnistus
  epäonnistuu pitkässä lauseessa; vaatii tapauskohtaista analyysia.
- Puhekieli vs. yleiskieli: sääntötason tulee olla herkkyydeltään
  yleiskielellinen mutta sietää puhekielen vakiintuneet muodot
  (esim. "me ollaan"). Kielitoimiston sanakirja[^ktk] ja VISK[^visk]
  ovat normilähteet; epävarmoissa tapauksissa ei liputeta.
- Yhdyssanavirheet vaativat sanastoresurssin (Kielitoimiston sanakirjan
  taivutustieto ei ole vapaasti lisensoitu - selvittämättä).

[^voikko]: Voikko - vapaat suomen kielen tarkistusohjelmat,
    https://voikko.puimula.org/ (libvoikko 4.3.3, 2025; voikko-fi 2.6,
    2026-04).
[^finngec]: Vu ym. (2026): FinnGEC. ACL Anthology (BEA-tyopaja),
    https://aclanthology.org/2026.bea-1.33/
[^creutz]: Creutz, M. (2024): Correcting Challenging Finnish Learner
    Texts With Claude, GPT-3.5 and GPT-4 Large Language Models.
    Helsingin yliopisto.
[^tdt]: Haverinen ym. (2014): Building the essential resources for
    Finnish: the Turku Dependency Treebank. Language Resources and
    Evaluation 48. UD-versio: https://universaldependencies.org/treebanks/fi_tdt/
[^tnpp]: TurkuNLP: Turku neural parser pipeline (poistunut kaytosta
    5/2024, seuraajasuositus Trankit),
    http://turkunlp.org/Turku-neural-parser-pipeline/
[^stanza]: Qi ym. (2020): Stanza: A Python Natural Language Processing
    Toolkit for Many Human Languages. ACL 2020 System Demonstrations,
    https://aclanthology.org/2020.acl-demos.14/
[^stanzalic]: Stanza: Performance and license information,
    https://stanfordnlp.github.io/stanza/performance.html
[^multiblimp]: Jumelet ym. (2026): MultiBLiMP 1.0: A Massively
    Multilingual Benchmark of Linguistic Minimal Pairs. TACL,
    https://aclanthology.org/2026.tacl-1.10/ (arXiv:2504.02768).
    Suomen osajoukko: SV-P 1670, SV-# 600, SP-# 300 paria,
    lähdeaineistoina UD_Finnish-TDT ja UD_Finnish-FTB.
[^ktk]: Kielitoimiston sanakirja, Kotimaisten kielten keskuksen
    nykysuomen sanakirja, https://kielitoimistonsanakirja.fi/
[^visk]: Hakulinen ym. (2004): Iso suomen kielioppi (VISK),
    verkkojulkaisu, https://kaino.kotus.fi/visk/ - esim. §1581
    (nesessiivirakenteen kongruenssi).
[^visk1284]: VISK §1284 Predikatiivin lukukongruenssin tyypit,
    https://scripta.kotus.fi/visk/sisallys.php?p=1284 ; §1285
    (numeraalisubjekti) https://scripta.kotus.fi/visk/sisallys.php?p=1285 ;
    Kielikello: Morfosyntaksi ja kielenhuolto,
    https://kielikello.fi/morfosyntaksi-ja-kielenhuolto-kirja-ja-puhekielen-rajankayntia/
    (kollektiivierisnimien yksikköpredikaatti sallittu 1977-).
[^trankit]: Trankit PyPI v1.1.2 (riippuvuudet: torch <=2.0.1, >=1.6.0),
    https://pypi.org/project/trankit/
