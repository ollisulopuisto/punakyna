"""NUM_NOUN_CASE (VISK §789, §773)."""
from punakyna.pipeline import check_text


def hits(t):
    return [s for s in check_text(t, use_spelling=False) if s.rule == 'NUM_NOUN_CASE']


def test_flagged():
    for t in ('Kolme lapsi leikkii pihalla.', 'Meillä on kaksi talo.',
              'Viisi kirja on pöydällä.', 'Kymmenen mies tuli.'):
        assert len(hits(t)) == 1, t


def test_correct_forms_not_flagged():
    for t in ('Kolme lasta leikkii pihalla.', 'Meillä on kaksi taloa.',
              'Viisi kirjaa on pöydällä.', 'Kymmenen miestä tuli.',
              'Kolmessa talossa asuu ihmisiä.', 'Yksi lapsi leikkii.',
              'Hän odotti kaksi tuntia.', 'Kello kaksi aamu valkeni.',
              'Kolme Viisasta tuli.', 'Kaksi, kolme päivää.',
              'Kuusi kuusi kasvoi pihalla.', 'Kaksi sataa euroa.'):
        assert not hits(t), t
