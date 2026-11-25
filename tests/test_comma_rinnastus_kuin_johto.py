"""PUNCT_COMMA_RINNASTUS, PUNCT_COMMA_KUIN, PUNCT_COMMA_JOHTOLAUSE:
ohjepankin pilkkusaannot paalauseiden valille, kuin-ilmauksiin ja
lainaus+johtolause -yhteyksiin (luetut 2026-11-25)."""
from punakyna.pipeline import check_text


def hits(t, rule):
    return [s for s in check_text(t, use_spelling=False) if s.rule == rule]


# --- PUNCT_COMMA_RINNASTUS ---

def test_missing_comma_between_full_main_clauses_is_flagged():
    for t, conj in (('Kesäkuussa ystävykset matkustelivat Yhdysvalloissa ja he olivat viikon Kanadassa.', 'ja'),
                    ('Koko maailmantilanne huolestuttaa kirjailijaa ja hän ei näe toivoa.', 'ja'),
                    ('Selvitys valmistuu alkusyksystä tai se siirtyy ensi vuoteen.', 'tai'),
                    ('Mies katsoi ulos ikkunasta ja Anna keitti kahvit keittiössä.', 'ja'),
                    ('Hän lähti aikaisin kotoa sillä oli jo myöhä.', 'sillä'),
                    ('Kirja myi hyvin ja kustantaja painoi lisää.', 'ja')):
        r = hits(t, 'PUNCT_COMMA_RINNASTUS')
        assert len(r) == 1, t
        assert r[0].replacements == [', ' + conj], t


def test_rinnastus_guards():
    for t in ('Kesäkuussa ystävykset matkustelivat Yhdysvalloissa, ja he olivat viikon Kanadassa.',
              # yhteinen subjekti
              'He menivät uimaan ja jäivät pitkäksi aikaa rannalle.',
              'Auto nostettiin ojasta aamulla ja hinattiin myöhemmin korjaamoon.',
              # 1./2. persoona: pilkku valinnainen
              'Tunsin itseni virkistyneeksi ja minä lähdin hyvillä mielin kotiin.',
              'Onnistuimme kokeilussa hyvin ja me saimme paljon palautetta.',
              # passiivi: pilkku valinnainen
              'Hakemukset osoitetaan johtajalle ja ne lähetetään hallintoyksikköön.',
              # hyvin lyhyet lauseet: pilkku valinnainen
              'Hän tuli ja hän näki.',
              # rinnastus ilman subjektia konjunktion jalkeen
              'Syötäväksi oli kalaa tai lihaa.',
              'Voit tulla tai jäädä kotiin.',
              # silla adessiivipronominina
              'Hän kirjoittaa sillä kynällä aina.',
              'Istuin sillä penkillä eilen.',
              # konjunktiopari
              'Hän sanoi, että ja tulihan hän.',
              # virkkeen alku
              'Ja hän tuli sittenkin.',
              'Sillä oli suuri merkitys.'):
        assert not hits(t, 'PUNCT_COMMA_RINNASTUS'), t


# --- PUNCT_COMMA_KUIN ---

def test_superfluous_comma_before_kuin_is_flagged():
    for t, fixed in (('Uusi opettaja on mukavampi, kuin entinen.', ' kuin'),
                     ('Todellisuus näyttää valoisammalta, kuin hän uskalsi toivoa.', ' kuin'),
                     ('Hän juoksee nopeammin, kuin minä.', ' kuin')):
        r = hits(t, 'PUNCT_COMMA_KUIN')
        assert len(r) == 1, t
        assert r[0].replacements == [fixed], t


def test_kuin_guards():
    for t in ('Uusi opettaja on mukavampi kuin entinen.',
              'Poika juoksee kuin nuori hirvi.',
              # irrallinen lisays: pilkku valinnainen
              'Marjapensas oli punainen, ikään kuin se olisi ollut liekeissä.',
              'Lue käyttöohje, ennen kuin käynnistät koneen.',
              'Hän teki niin, kuin itse parhaaksi katsoi.',
              # ei pilkkua ollenkaan
              'Toisin kuin monet luulevat, hän ei ole varakas.',
              # pilkku muualla kuin heti kuin-sanan edella
              'Kesä oli kuuma, ja helle kesti kuin loppumatonta viikkoa.'):
        assert not hits(t, 'PUNCT_COMMA_KUIN'), t


# --- PUNCT_COMMA_JOHTOLAUSE ---

def test_missing_comma_after_quote_before_johtolause_is_flagged():
    for t in ('\u201dEn aio erota tehtävästäni\u201d ministeri vastasi.',
              '\u201dTulen huomenna\u201d hän sanoi.',
              '"Asia selvitetään" kunnanjohtaja totesi kokouksessa.'):
        r = hits(t, 'PUNCT_COMMA_JOHTOLAUSE')
        assert len(r) == 1, t


def test_johtolause_guards():
    for t in ('\u201dEn aio erota tehtävästäni\u201d, ministeri vastasi.',
              # kysymys- ja huutomerkki: ei pilkkua
              '\u201dEroaisitko?\u201d ministeri kysyi.',
              '\u201dEn eroa!\u201d ministeri huudahti.',
              # kolme pistetta: pilkku valinnainen
              '\u201dEn eroa...\u201d vakuutteli hän.',
              # johtolause keskella, pilkut kunnossa
              '\u201dEn aio erota\u201d, ministeri totesi, \u201dmutta harkitsin sitä.\u201d',
              # ei johtolausetta
              'Hän käytti sanaa \u201dpunakynä\u201d puhuessaan oikoluvusta.'):
        assert not hits(t, 'PUNCT_COMMA_JOHTOLAUSE'), t
