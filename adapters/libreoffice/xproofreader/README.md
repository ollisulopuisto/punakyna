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
