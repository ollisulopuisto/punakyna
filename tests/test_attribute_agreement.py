"""ATTR_AGREEMENT (VISK §1267-1268): laatusanaattribuutin luku."""
from punakyna.pipeline import check_text


def hits(t):
    return [s for s in check_text(t, use_spelling=False) if s.rule == 'ATTR_AGREEMENT']


def test_flagged():
    for t in ('Isot talo seisoi mäellä.', 'Hyvä ruoat maistuvat.',
              'Pihalla oli vanhat puu.'):
        assert len(hits(t)) == 1, t


def test_correct_forms_not_flagged():
    for t in ('Isot talot seisoivat mäellä.', 'Hyvä ruoka maistuu.',
              'Pihalla oli vanha puu.', 'Talo on iso.', 'Moni talo paloi.',
              'Useat ihmiset tulivat.', 'Iso, vanha talo.',
              'Suomen kaunis luonto.', 'Pitkä kesä on ohi.'):
        assert not hits(t), t
