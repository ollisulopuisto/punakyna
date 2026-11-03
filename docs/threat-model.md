# Punakynä: uhkamalli ja rajat (2026-11-03)

## Peruslupaus
Teksti ei lähde koneelta oletuksena. Palvelin sitoutuu loopbackiin,
vaatii tunnuksen, ei logaa tekstisisältöä, ei lähetä CORS-otsakkeita.

## Mikä on suojattu - ja mikä EI

### Selainkanava (native messaging)
- Selaimen manifestin allowed_origins/allowed_extensions rajoittaa,
  mitkä LAAJENNUKSET selain sallii käynnistävän isäntäprosessin.
  Selain valvoo listaa. Peruutus = manifestin poisto.
- Bearer-tunnus pysyy isäntäprosessissa; se ei koskaan selaimen JS:ään.
- RAJA: manifesti suojaa vain selainkanavan. Se EI ole yleinen
  sovelluskohtainen valtuutus rajapinnalle.

### Paikallinen HTTP-rajapinta (kaikki muut asiakkaat)
- Yksi jaettu tunnustiedosto todentaa KAIKKI ei-selain-asiakkaat
  (CLI, LO-sovitin, tulevat työkalut). Ei sovelluskohtaista
  valtuutusta tai peruutusta: sama tunnus = samat oikeudet.
- Kuka tahansa paikallinen käyttäjätilin prosessi, joka lukee
  ~/.config/punakyna/token (0600, käyttäjän oma), voi kutsua
  rajapintaa ja lähettää sille tekstiä.
- Kuka tahansa paikallinen prosessi voi myös SUORITTAA
  native_host.py:n suoraan (se on tavallinen ohjelma) - manifestin
  rajoitus koskee vain selaimen käynnistysreittiä.
- Yleinen per-app enrollment/peruutus (erilliset tunnukset per sovellus,
  auditointi, peruutuslista) on TIETOISESTI TEKEMÄTTÄ. Se on
  ennakkoedellytys ennen kuin rajapintaa voi kutsua turvalliseksi
  kolmansien osapuolten integroinnille.
- Torjutut hyökkäykset: DNS-rebinding (Host-tarkistus), selaimen
  cross-origin simple requestit (vain application/json + ei CORS:ia),
  tunnuksen kalastelu redirecteillä (asiakas ei seuraa), proxy-vuoto
  (asiakas ohittaa ympäristöproxyt loopbackille), ääretön kuorma
  (yhteys- ja työrajat, aikakatkaisut, kokorajat).

### Uhkia joita EI torjuta (tietoiset rajat)
- Paikallinen haitakeprosessi samalla käyttäjätunnuksella: voi lukea
  tunnuksen, kutsua rajapintaa, tai ajaa moottorin suoraan.
  Loopback-palvelu ei voi erottaa "hyvää" ja "pahaa" paikallista
  prosessia ilman alustan tukea (esim. macOS XPC + koodiallekirjoitus).
- Tekstin luottamuksellisuus muihin suuntaan: mitään ei LÄHETETÄ
  ulos, mutta rajapintaa kutsuva prosessi valitsee itse tekstinsä.

## Sovelluskohtainen todennus (osittainen enrollment, 2026-11-03)
- tokenfile.load_or_create_app_token: jokaiselle sovellukselle oma
  tunnustiedosto ~/.config/punakyna/tokens/<sovellus> (0600, atomisesti).
- Palvelin hyväksyy minkä tahansa rekisteröidyn tunnuksen (token_map);
  peruutus = tiedoston poisto + palvelimen uudelleenkäynnistys.
- RAJAT: tunnuksia ei vielä sidota oikeuksiin (kaikilla samat
  oikeudet), ei audit-lokia, eikä käyttäjän hyväksyntädialogia -
  tämä on perusta, ei valmis enrollment-UX. Paikallinen haitake
  samalla tunnuksella pysyy hyväksyttynä uhkana.
