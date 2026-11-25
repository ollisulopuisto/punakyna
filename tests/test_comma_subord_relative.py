"""PUNCT_COMMA_SUBORD ja PUNCT_COMMA_RELATIVE: puuttuva pilkku ennen
alistuskonjunktiota tai joka/mika-relativiivia (ohjepankki, luettu 2026-11-25)."""
from punakyna.pipeline import check_text


def hits(t, rule):
    return [s for s in check_text(t, use_spelling=False) if s.rule == rule]


def test_missing_comma_before_subordinate_conjunction_is_flagged():
    for t, conj in (('Mies sanoi että tulee huomenna.', 'että'),
                    ('Hän toivoo että sää paranee.', 'että'),
                    ('Hän ei tullut koska oli väsynyt.', 'koska'),
                    ('Ilmoita meille kun olet perillä.', 'kun'),
                    ('Aloitamme nyt jos hän saapuu ajoissa.', 'jos'),
                    ('Hän tuli vaikka oli kipeä.', 'vaikka'),
                    ('Odota rauhassa kunnes valo syttyy.', 'kunnes'),
                    ('Puhu hiljaa jotta vauva ei herää.', 'jotta'),
                    ('Sanoin hänelle mikäli muistat asian.', 'mikäli'),
                    ('Tule meille joskin olet kiireinen.', 'joskin')):
        r = hits(t, 'PUNCT_COMMA_SUBORD')
        assert len(r) == 1, t
        assert r[0].replacements == [', ' + conj], t
        assert r[0].severity == 'warning', t


def test_subordinate_comma_guards():
    for t in ('Mies sanoi, että tulee huomenna.',
              # virkkeen alku
              'Kun sataa, ei kannata lähteä ulos.',
              'Jos opetussuunnitelma muuttuu, opiskelijalta voi vaatia lisää.',
              # yhden sanan paalause: pilkku valinnainen
              'Toivon että tulet ajoissa.',
              'Tiedätkö sataako tänään?',
              # konjunktioparit
              'En ollut kuullut asiasta, mutta jos olisin tiennyt, olisin vihainen.',
              'Perheessämme sanotaan, että kun menee kylläisenä nukkumaan, näkee unia.',
              'Pyysin puheenvuoroa, mutta vaikka nousin seisomaan, ei puheenjohtaja huomannut.',
              # korostussana: pilkku voi olla sen edella
              'Palauttaminen voi olla hankalaa, varsinkin jos yritys sijaitsee ulkomailla.',
              'Lääkelasku tuntuu suurelta etenkin, jos lääkkeitä on paljon.',
              # korrelaatti seka ... etta
              'Tilaisuuteen osallistuivat sekä asiakkaiden että työntekijöiden edustajat.',
              # idioomi
              'Mitä jos hän ei tulekaan?',
              # paitsi/heti/myös + konjunktio: pilkku korostussanan edella
              'Kielto ei koske vaihtoa, paitsi jos tilanteessa tuomitaan rangaistus.',
              'Pelaajat palaavat kentälle heti kun rangaistus loppuu.',
              'Sääntö pätee, myös mikäli pelaaja jatkaa peliä.',
              # raja-merkki valissa
              'Hän sanoi: että asia on kunnossa.'):
        assert not hits(t, 'PUNCT_COMMA_SUBORD'), t


def test_missing_comma_before_relative_is_flagged():
    for t, rel in (('Auto joka ajoi ohi oli punainen.', 'joka'),
                    ('Perhe aloitti projektin josta ei tullut loppua.', 'josta'),
                    ('Tutkimuksissa ei löytynyt poikkeavaa mikä ei yllättänyt.', 'mikä'),
                    ('Hän lainasi kirjoja joita oli lainannut aiemminkin.', 'joita'),
                    ('On maita joissa viesti ymmärretään väärin.', 'joissa'),
                    ('Oppilaat joiden opettajat kokivat työn imua viihtyivät.', 'joiden'),
                    ('Mies jonka näin eilen on naapurini.', 'jonka'),
                    ('Kerro minulle mitä tapahtui eilen illalla.', 'mitä'),
                    ('Tämä on se paikka missä tapahtuma sattui.', 'missä')):
        r = hits(t, 'PUNCT_COMMA_RELATIVE')
        assert len(r) == 1, t
        assert r[0].replacements == [', ' + rel], t


def test_relative_comma_guards():
    for t in ('Auto, joka ajoi ohi, oli punainen.',
              'Perhe aloitti rakennusprojektin, josta ei tullut loppua.',
              'Tutkimuksissa ei löytynyt mitään poikkeavaa, mikä ei yllättänyt.',
              # virkkeen alku
              'Joka tapauksessa asia selvitetään.',
              'Mikä on tilanne?',
              # joka/mika maaraissanana: seuraava sana on nomini
              'Hän käy töissä joka päivä.',
              'Joka vuosi kilpailu järjestetään uudelleen.',
              'Hän soittaa joka kerta myöhässä.',
              'Joka toinen auto oli pysäköity väärin.',
              # konjunktiopari: "mita teit ja mita nait"
              'Kerro, mitä teit ja mitä näit.',
              'Kysyin, mitä tapahtui tai mitä olin kuullut.',
              # yleispronomini-idioomit
              'Peliaika voi olla periaatteessa mikä tahansa.',
              'Kuka tahansa voi käyttää pakettia mihin tahansa tarkoitukseen.',
              # erisnimi, ei relatiivipronomini
              'Yhtiön pohjalta Jolla kehitti uuden käyttöjärjestelmän.',
              # raja-merkki valissa
              'Hän sanoi: mitä teit eilen?'):
        assert not hits(t, 'PUNCT_COMMA_RELATIVE'), t


def test_relative_with_subject_right_after_is_recall_limit():
    # "auto joka mies osti": seuraava sana on nomini -> ohitetaan
    # (tarkkuusrajoitus, ks. rules.py _REL_QUANT)
    assert not hits('Auto joka mies osti oli vanha.', 'PUNCT_COMMA_RELATIVE')
    # mutta taivutetut muodot liputetaan aina
    assert len(hits('Auto jonka mies osti oli vanha.', 'PUNCT_COMMA_RELATIVE')) == 1
