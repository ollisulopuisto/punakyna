# -*- coding: utf-8 -*-
"""TYPO_QUOTE_MARK: suorat lainausmerkit -> kaarevat ”.

Lähde: ohjepankki, "Lainausmerkit" (luettu 2026-11-25): suomenkielisessä
tekstissä käytetään kaarevia lainausmerkkejä; merkki kiinni sanassa ilman
välilyöntiä.
"""
from punakyna.pipeline import check_text


def _hits(text, rule='TYPO_QUOTE_MARK'):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == rule]


def test_straight_quotes_flagged_and_fixed():
    r = _hits('Hän sanoi "Tule tänne" heti.')
    assert len(r) == 2
    assert all(s.replacements == ['\u201d'] for s in r)


def test_straight_quotes_around_title_flagged():
    r = _hits('Elokuva "Tuntematon sotilas" kertoo sodasta.')
    assert len(r) == 2


def test_curly_quotes_not_flagged():
    assert not _hits('Hän sanoi \u201dTule tänne\u201d heti.')


def test_inch_mark_not_flagged():
    assert not _hits('Ruutu on 15" levyinen.')
    assert not _hits('Sarja alkoi 15".30 ja päättyi 16".15.')
