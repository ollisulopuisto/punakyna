# -*- coding: utf-8 -*-
"""WORD_KUN_KUIN: vaihtumattoman sanaliiton kun/kuin-valinta."""
from punakyna.pipeline import check_text


def hits(text):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == 'WORD_KUN_KUIN']


def test_ennen_kun_flagged():
    s = hits('Muista soittaa ennen kun lähdet.')
    assert len(s) == 1
    assert s[0].replacements == ['kuin']


def test_niin_kun_flagged():
    s = hits('Hän teki niin kun häntä käskettiin.')
    assert len(s) == 1
    assert s[0].replacements == ['kuin']


def test_sama_erilainen_kun_flagged():
    for t in ('Kirja on erilainen kun elokuva.',
              'Hän ajattelee sama kun minäkin.',
              'Näkemys on aivan kun minulla.'):
        s = hits(t)
        assert len(s) == 1, t
        assert s[0].replacements == ['kuin'], t


def test_more_kuin_to_kun_flagged():
    for t in ('Heti kuin saavuin, aloin työskennellä.',
              'Sen jälkeen kuin sade lakkasi, lähdimme ulos.',
              'Silloin kuin olin lapsi, asuin maalla.'):
        s = hits(t)
        assert len(s) == 1, t
        assert s[0].replacements == ['kun'], t


def test_correct_forms_not_flagged():
    for t in ('Muista soittaa ennen kuin lähdet.',
              'Hän teki niin kuin häntä käskettiin.',
              'Aina kun tulen, hän tervehtii.',
              'Kirja on erilainen kuin elokuva.'):
        assert hits(t) == [], t


def test_comma_between_blocks_flag():
    assert hits('Hän teki niin, kun käskettiin.') == []
    assert hits('Hän tuli aina, kuin ehti.') == []


def test_both_allowed_not_flagged():
    for t in ('Samaan aikaan kun saavuin, hän lähti.',
              'Samaan aikaan kuin saavuin, hän lähti.',
              'Sitä mukaa kun tulevat, ne menevät.',
              'Sitä mukaa kuin tulevat, ne menevät.',
              'Hän lähti samalla kuin muutkin.',
              'Odotin niin kauan kun jaksoin.'):
        assert hits(t) == [], t


def test_aina_kuin_comparison_not_flagged():
    from punakyna.pipeline import check_text
    for t in ('Hän on aina kuin lapsi.', 'Se näyttää aina kuin uudelta.'):
        assert [s for s in check_text(t, use_spelling=False, use_gc=False)
                if s.rule == 'WORD_KUN_KUIN'] == [], t
