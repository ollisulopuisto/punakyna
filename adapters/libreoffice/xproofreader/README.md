# Punakynä XProofreader (LibreOffice)

Natiivi LibreOffice-kieliopintarkistus (Tools -> Options -> Language
Settings -> Writing Aids -> Punakynä). Komponentti on ohut asiakas
paikalliselle Punakynä-API:lle - teksti ei lähde koneelta.

## Käyttöönotto (käyttäjän toimenpiteet, ei automaattista asennusta)

1. Käynnistä palvelin: `python -m punakyna --serve`
2. Rekisteröi sovellustunnus: `python -m punakyna --enroll-app libreoffice`
3. Rakenna: `python3 make_oxt.py` -> punakyna-proofreader.oxt
4. Asenna LibreOfficeen: Työkalut -> Lisäosien hallinta -> Lisää
   (tai `unopkg add punakyna-proofreader.oxt`)
5. Ota käyttöön: Työkalut -> Asetukset -> Kieliasetukset ->
   Kirjoituksen apuvälineet -> Punakynä

Peruutus: `python -m punakyna --revoke-app libreoffice` (voimassa heti,
ei palvelimen uudelleenkäynnistystä) ja/tai lisäosan poisto.

Vaatimukset: LibreOffice Python-UNO:lla (Linux-jakeluissa vakio,
python3-uno). Ei verkkoyhteyttä muualle kuin 127.0.0.1.

Jos palvelin ei ole käynnissä tai sovellustunnus puuttuu, kappaleen
alkuun ilmestyy sininen ohjevirhe, joka kertoo puuttuvan vaiheen
(--serve / --enroll-app) - asennusvika ei jää hiljaiseksi
"ei virheitä" -tilaksi. Ohje ei sisällä tunnusta eikä tekstiä.

## Suomen oikeinkirjoituksen sanasto ja Voikko-rinnakkaisuus

LO:n taustaoikoluku (aaltoviivat kirjoitettaessa) vaatii profiiliin
jonkin suomen oikeinkirjoitustarkistimen. Suositus: Voikko
(esim. `libreoffice-voikko`-paketti tai LibreOfficen laajennos).
HUOM: Voikko-laajennoksen asennus kirjoittaa oletusasetuksen
(GrammarCheckerList/fi-FI) korvaavasti, mika voi poistaa Punakynan
kaytosta - ota Punakyna silloin uudelleen kayttoon Writing Aids
-asetuksista (kohta 5). Punakyna ei koskaan muuta muiden
tarkistimien asetuksia.

Todennettu hiekkalaatikossa (GUI-testi tests/test_lo_writer_background.py):
kirjoitusvirheiden punaiset aaltoviivat (Voikko) JA Punakynan
kielioppivirheen sininen alleviivaus + oikolukudialogin selite ja
korjausehdotus (esim. "Me olen likaisia." -> "olemme").

## macOS (varmistamatta - ei testattu Macilla)

Seuraavat polut ovat parhaita arvauksia LibreOffice.app-paketin
rakenteesta; varmista ensimmäisellä Mac-asennuksella ja korjaa tämä
ohje havaintojen mukaan:

- LibreOfficen oma Python-UNO-tulkki:
  `/Applications/LibreOffice.app/Contents/Resources/python`
  (tai `.../Contents/Frameworks/LibreOfficePython.framework/...`
  versiosta riippuen)
- unopkg: `/Applications/LibreOffice.app/Contents/MacOS/unopkg`
- Asennus muutoin samat vaiheet kuin yllä: palvelin päälle, tunnus
  (`--enroll-app libreoffice`), .oxt rakennetaan make_oxt.py:llä ja
  lisätään LibreOfficen lisäosien hallinnasta.
- Huom: macOS:n oma oikoluku (NSSpellServer-sovitin,
  `adapters/macos/`) on erillinen, vielä kääntämätön luonnos - se ei
  ole edellytys LibreOffice-lisäosalle.
