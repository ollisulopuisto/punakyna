"""PERFECT_PASSIVE_PARTICIPLE: "olen menty" -> "olen mennyt" (VISK §1292, §530)."""
from punakyna.pipeline import check_text


def hits(text):
    return [s for s in check_text(text, use_spelling=False)
            if s.rule == 'PERFECT_PASSIVE_PARTICIPLE']


def test_user_sentence_flagged():
    h = hits('Minä olen menty kotiin.')
    assert len(h) == 1
    assert (h[0].start, h[0].end) == (10, 15)
    assert h[0].replacements == ['mennyt']


def test_other_persons_and_plural_replacement():
    assert hits('He ovat menty kotiin.')[0].replacements == ['menneet']
    assert hits('Me olemme tultu myöhään.')[0].replacements == ['tulleet']
    assert hits('Sinä olet jo käyty siellä.')[0].replacements == ['käynyt']
    assert hits('Minä en ole menty.')[0].replacements == ['mennyt']
    assert hits('Minä olin menty kotiin.')


def test_genuine_passive_perfect_not_flagged():
    for s in ('Kotiin on menty.', 'On menty kotiin.', 'Sohvalla on istuttu.',
              'Kaikki on jo käyty läpi.', 'Ei ole menty kotiin.',
              'Eilen ei oltu menty.'):
        assert not hits(s), s


def test_correct_active_perfect_not_flagged():
    for s in ('Minä olen mennyt kotiin.', 'He ovat menneet kotiin.',
              'Me olemme tulleet.', 'Minä en ole mennyt.'):
        assert not hits(s), s


def test_transitive_passive_participle_predicative_left_alone():
    # kelvollisia predikatiiveja: transitiivin TU-partisiippi
    for s in ('Olen kiusattu koulussa.', 'Olemme petetty.',
              'He ovat hylätty.', 'Olen tehty puusta.'):
        assert not hits(s), s


def test_clitic_bearing_participle_flagged():
    # Devin #45: "mentykin" ei saa kadota esisuodattimeen (vaatii libvoikko).
    h = hits('Minä olen mentykin kotiin.')
    assert len(h) == 1
    assert h[0].replacements == ['mennytkin']
