# macOS-järjestelmäintegraatio: tutkimus ja suunnitelma (2026-11-03)

## Keskeinen löydös: suomen oikeinkirjoitus on JO saatavilla macOS:ään

VoikkoSpellService (walokra/osxspell, GPL-3.0, https://github.com/walokra/osxspell)
rekisteröi Voikon NSSpellServer-palveluksi: toimii macOS 12+:lla, asennus
`brew install --cask voikkospellservice` (https://formulae.brew.sh/cask/voikkospellservice).
Tämä on hyödyllinen VERTAILUKOHTA, ei todiste että Punakynällä ei olisi
oikeinkirjoitusarvoa: Punakynä tarjoaisi oikeinkirjoituksen JA kieliopin
yhdestä palvelusta. Historiallinen blogi (verteksi.net 2010) kertoo
VoikkoSpellServicen kielioppitarkistuksen EI toimineen
("Kieliopintarkistus ei toimi...").

## Mekanismi: NSSpellServer (edelleen tuettu)

Apple developer.apple.com/documentation/foundation/nsspellserver +
arkistoitu Spell Checking Programming Topics:
- Palvelinohjelma: NSSpellServer, registerLanguage:byVendor:
  (esim. "Finnish" byVendor:"Punakynä") -> näkyy oikolukupaneelissa
  "Finnish (Punakynä)".
- Delegaatti: spellServer:findMisspelledWordInString:language:wordCount:countOnly:
  ja spellServer:suggestGuessesForWord:inLanguage:; kieliopille oma
  checkGrammarInString-delegaattimetodi.
- Rekisteröinti: .service-bundle käyttäjän ~/Library/Services/ -hakemistoon
  + services-deskriptori. Käyttäjätason asennus, palautettavissa (poisto).
- Käyttäjä valitsee tarkistimen Spelling-paneelin popupista: Punakynä EI
  korvaa oletusta vaan on vaihtoehto.

Moderni ennakkotapaus: Divvun MacDivvun.service
(https://github.com/divvun/macdivvun-service) - NSApplication hostaa
NSSpellServeria, macOS 12+, per-kieli grammar-sääntöjen togglaukset.
Todistaa reitin toimivan nyky-macOS:lla.

## Turvallisuushuomiot (DirtyDict, wts.dev 2025-12)

NSSpellServer perustuu vanhentuneeseen Distributed Objects -mekanismiin ja
siinä oli 2025 polkujen käsittelyn CVE:t (CVE-2025-43266/-43190/-43518);
Apple paikkasi itse API:n. Kolmannen osapuolen palvelinten tulee silti
pitää delegaattipinta minimissä: ei tiedostopolkujen tulkintaa
pyynnöistä, vain merkkijonojen tarkistus. Lähde: wts.dev/posts/dirtydict/

## Ehdotettu arkkitehtuuri (EI vielä toteutettu, ei Mac-testiä)

Punakyna.service (~ Library/Services, käyttäjän hyväksynnällä):
- Ohut Swift/ObjC-isäntä: NSSpellServer-delegaatti, joka kutsuu
  paikallista HTTP-rajapintaa (127.0.0.1, bearer-tunnus) TAI suoraan
  libvoikkoa; API-reitti uudelleenkäyttää kovennukset ja moottorilukon.
- MOLEMMAT kyvyt mukana missä tuettu: oikeinkirjoitus
  (findMisspelledWordInString/suggestGuessesForWord) JA kielioppi
  (checkGrammar-delegaatti). Kieliopin delegaatin toimivuus
  nyky-macOS:lla on AVOIN KYSYMYS (historiallisesti kaatunut) -
  vahvistetaan ensimmäisellä Mac-testillä. Kielivalinta
  "Finnish (Punakynä)".
- Delegaatin paluuarvot: NSRange-positiot ovat UTF-16-yksiköitä -
  sama muunnos kuin LO-sovittimessa (adapters/libreoffice/offsets.py).
- Asennus: kopioi bundle ~/Library/Services + uudelleenkirjautuminen /
  NSUpdateDynamicServices. Ei tehdä ilman käyttäjän lupaa.

Avoimet: kieliopin checkGrammar-delegaatin toimivuus nyky-macOS:lla
(historiallinen kaatuminen), notarointi/allekirjoitus (maksullinen
kehittäjätili?), hiekkalaatikon rajat.
