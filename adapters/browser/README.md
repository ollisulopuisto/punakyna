# Selainsovitin: native messaging (valittu arkkitehtuuri)

## Päätös ja perustelut

Selainlaajennos ei puhu HTTP:tä paikalliselle rajapinnalle. Vaihtoehdot olivat:

a) **Native messaging (valittu)**: selain käynnistää paikallisen
   isäntäprosessin (native_host.py) ja puhuu stdio-kehystettyä JSON:ia.
   - Ei CORS-/Origin-ongelmia ollenkaan (ei HTTP:ta selaimesta).
   - Bearer-tunnus pysyy isäntäprosessissa - ei koskaan selaimen JS:ään,
     josta se voisi vuotaa sivustoille.
   - Enrollment (VAIN selainkanavalle): manifestin
     allowed_origins/allowed_extensions listaa tasan ne laajennukset,
     jotka saavat käynnistää isännän. Selain itse valvoo listaa.
     Peruutus = manifestin poisto. HUOM: tämä EI ratkaise rajapinnan
     yleistä sovelluskohtaista valtuutusta - ks. docs/threat-model.md.
   - Palautettavissa kokonaan: ei asennusta järjestelmään, vain yksi
     JSON-tiedosto käyttäjän selainprofiiliin.

b) Tarkka-Origin CORS + todennettu enrollment HTTP-rajapinnassa:
   vaatii uuden enrollment-protokollan rakentamista ja jättää HTTP-pinnan
   selaimelle; laajempi hyökkäyspinta ilman lisähyötyä.

## Manifestin sijainnit (käyttäjätaso, ei pääkäyttäjää)

- Chrome macOS: ~/Library/Application Support/Google/Chrome/NativeMessagingHosts/fi.punakyna.host.json
- Firefox macOS: ~/Library/Application Support/Mozilla/NativeMessagingHosts/fi.punakyna.host.json
- Chrome Linux: ~/.config/google-chrome/NativeMessagingHosts/
- Firefox Linux: ~/.mozilla/native-messaging-hosts/

Manifestissa path osoittaa native_host.py:hen ja allowed_origins/
allowed_extensions TÄSMÄLLEEN rekisteröidyn laajennuksen tunnukseen.
Käyttäjä ei ole vielä hyväksynyt rekisteröintiä: manifestia ei kirjoiteta
ennen hyväksyntää. Laajennusta itseään ei ole vielä rakennettu.
