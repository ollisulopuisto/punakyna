"""SV_NUMBER_NONOLLA (VISK §1267-1270) ja PERFECT_PASSIVE_PARTICIPLE-taulukon eheys."""
import pytest

from punakyna.backend_voikko import get_voikko
from punakyna.pipeline import check_text
from punakyna.rules import _INTRANSITIVE_NUT


def hits(text, rule='SV_NUMBER_NONOLLA'):
    return [s for s in check_text(text, use_spelling=False) if s.rule == rule]


def test_singular_subject_plural_verb_flagged():
    for s in ('Lapsi leikkivät pihalla.', 'Opettaja tulevat huomenna.',
              'Poika menevät kouluun.'):
        h = hits(s)
        assert len(h) == 1, s
        assert h[0].severity == 'warning'


def test_valid_and_colloquial_not_flagged():
    for s in ('Lapset leikkivät pihalla.',          # oikein
              'Lapset leikkii pihalla.',            # puhekieli, ei liputeta
              'Lapsi ja opettaja leikkivät.',       # koordinoitu subjekti
              'Poika sekä tyttö menevät kouluun.',
              'Lapsi, joka leikkii, ja he menevät.',
              'Kaikki menevät kotiin.',
              'Hän ja poika tulevat huomenna.',
              'Helsingin Sanomat kirjoittavat siitä.',
              'Lapsen kanssa leikkivät kaikki.'):
        assert not hits(s), s


def test_olla_left_to_olla_rule():
    assert not hits('Lapsi ovat kotona.')  # SV_AGREEMENT hoitaa


@pytest.mark.parametrize('verb', sorted(_INTRANSITIVE_NUT))
def test_nut_table_entries_are_real_active_participles(verb):
    """Jokainen taulukon muoto on Voikon mukaan kyseisen verbin NUT-partisiippi."""
    v = get_voikko()
    sg, pl = _INTRANSITIVE_NUT[verb]
    a_sg = v.analyze(sg)
    a_pl = v.analyze(pl)
    assert any(a.get('PARTICIPLE') == 'past_active' and a.get('NUMBER') == 'singular'
               for a in a_sg), (verb, sg)
    assert any(a.get('PARTICIPLE') == 'past_active' and a.get('NUMBER') == 'plural'
               for a in a_pl), (verb, pl)
    assert any((a.get('BASEFORM') or '').lower() == sg for a in a_sg)
    assert any((a.get('BASEFORM') or '').lower() == sg for a in a_pl)


def test_regressions_from_wikipedia_sweep():
    # numerot ennen sanaa: koordinaatio ei nay sanatokeneina
    assert not hits('Itäpuolelle. 34. ja 50. Armeijakunta hyökkäsivät suoraan.')
    assert hits('Lapsi leikkivät pihalla. Opettaja tulevat.')
    assert not hits('Viipurissa 3. ja 5. divisioona menettivät alueet.')
    # kopula sopii predikatiivin kanssa
    assert not hits('Merkittävä tekijä olivat vuosina 1937 tehdyt päätökset.')
