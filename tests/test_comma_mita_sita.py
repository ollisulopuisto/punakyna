# -*- coding: utf-8 -*-
"""PUNCT_COMMA_MITA_SITA: tasapainoisen sanaparin jäsenten välinen pilkku."""
from punakyna.pipeline import check_text


def hits(text):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == 'PUNCT_COMMA_MITA_SITA']


def test_mita_sita_missing_comma():
    s = hits('Mitä korkeammalla aurinko on sitä enemmän altistumme '
             'ultraviolettisäteilylle.')
    assert len(s) == 1
    assert ', sitä' in s[0].message


def test_toisaalta_pair_missing_comma():
    s = hits('Toisaalta kirjassa on paljon hyvää toisaalta se voisi olla '
             'vielä paljon parempikin.')
    assert len(s) == 1
    assert ', toisaalta' in s[0].message


def test_milloin_pair_missing_comma():
    s = hits('Hän kannattaa milloin uusia milloin vanhoja suosituksia.')
    assert len(s) == 1
    assert ', milloin' in s[0].message


def test_yhtaalta_toisaalta_missing_comma():
    s = hits('Hän halusi yhtäältä jäädä toisaalta lähteä.')
    assert len(s) == 1


def test_comma_present_no_flag():
    assert hits('Mitä korkeammalla aurinko on, sitä enemmän '
                'altistumme ultraviolettisäteilylle.') == []
    assert hits('Toisaalta kirjassa on paljon hyvää, toisaalta se voisi '
                'olla parempikin.') == []


def test_plain_question_no_flag():
    assert hits('Mitä sinä teet huomenna illalla?') == []
    assert hits('Mitä sitä nyt turhaan huolehtimaan.') == []


def test_single_adverb_no_flag():
    assert hits('Toisaalta asia on monimutkainen.') == []
    assert hits('Hän tuli osaksi tiimiä viime vuonna.') == []
    assert hits('Milloin tulet kotiin?') == []


def test_mita_sita_replacement():
    s = hits('Mitä enemmän harjoittelet sitä parempi tuloksista tulee.')
    assert len(s) == 1
    assert s[0].replacements == [', ']
