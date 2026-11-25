# -*- coding: utf-8 -*-
"""PUNCT_COMMA_TITLES: perusmuotoisten titteleiden välissä on pilkku.

Lähde: ohjepankki, "Pilkku titteleiden välissä: johtaja, insinööri Virta"
(luettu 2026-11-25). Kun ensimmäisellä tittelillä on oma määrite
("laitoksen johtaja"), pilkku on valinnainen, joten vain kahden
perusmuotoisen tittelin suora peräkkäisyys liputetaan.
"""
from punakyna.pipeline import check_text


def _hits(text, rule='PUNCT_COMMA_TITLES'):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == rule]


def test_two_bare_titles_without_comma_flagged():
    for t in ('Juhlapuheen pitää toimitusjohtaja ekonomi Liisa '
              'Järvinen.',
              'Kommenttipuheenvuoron esittää lehtori FT Kaisa Karvinen.',
              'Palkinnon luovuttaa rehtori maisteri Jussi Korhonen.'):
        r = _hits(t)
        assert len(r) == 1, t


def test_titles_with_comma_not_flagged():
    for t in ('Juhlapuheen pitää toimitusjohtaja, ekonomi Liisa '
              'Järvinen.',
              'Kommenttipuheenvuoron esittää lehtori, FT Kaisa '
              'Karvinen.'):
        assert not _hits(t), t


def test_single_title_and_modified_title_not_flagged():
    for t in ('Johtaja Virtanen otti valtuuston vastaan.',
              'Laitoksen johtaja tohtori Orvokki Virtanen otti '
              'valtuuston vastaan aamupäivällä.',
              'Hän lähetti kirjeen lukion rehtorille maisteri '
              'Heinoselle.'):
        assert not _hits(t), t


def test_ordinary_noun_pairs_not_flagged():
    for t in ('Hän on opettaja ja valmentaja.',
              'Ministeri puhui lehdistölle.',
              'Koulu tarvitsee opettaja Virran kaltaisia ihmisiä.'):
        assert not _hits(t), t
