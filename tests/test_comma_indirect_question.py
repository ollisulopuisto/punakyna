# -*- coding: utf-8 -*-
"""PUNCT_COMMA_INDIRECT_QUESTION: epäsuora kysymyslause erotetaan pilkulla.

Lähde: ohjepankki, "Pilkku ja epäsuora kysymyslause: Hän kysyi, tulenko
ajoissa." (luettu 2026-11-25).
"""
from punakyna.pipeline import check_text


def _hits(text, rule='PUNCT_COMMA_INDIRECT_QUESTION'):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == rule]


def test_missing_comma_before_indirect_question_flagged():
    for t in ('En tiedä missä hän nykyisin asuu.',
              'Kukaan ei taida tietää miten työ tänään sujuu.',
              'Näistä merkeistä voi ennustaa tuleeko tyttö vai poika.',
              'Muistatko mitä sanoimme eilen?'):
        r = _hits(t)
        assert len(r) == 1, t


def test_ko_verb_indirect_question_flagged():
    assert len(_hits('Hän kysyi saako täältä kahvia.')) == 1
    assert len(_hits('En tiedä onko huomiseksi luvassa sadetta.')) == 1


def test_comma_already_present_not_flagged():
    for t in ('En tiedä, missä hän asuu.',
              'Hän kysyi, tulenko ajoissa.',
              'On kyseenalaista, toteutuuko suunnitelma koskaan.'):
        assert not _hits(t), t


def test_relative_and_other_constructions_not_flagged():
    for t in ('Se on jotain mitä en ymmärrä.',
              'Hän sanoi että tulee huomenna.',
              'Paikka missä hän asuu on kaukana.',
              'Tiedätkö sinä sen?'):
        assert not _hits(t), t


def test_question_word_as_sentence_final_adverbial_not_flagged():
    assert not _hits('En muista milloin.')
