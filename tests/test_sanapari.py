# -*- coding: utf-8 -*-
"""TYPO_SANAPARI: kiteytyneen sanaparin yhteen/erilleen kirjoitus."""
from punakyna.pipeline import check_text


def hits(text):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == 'TYPO_SANAPARI']


def test_joined_form_flagged():
    s = hits('Itseasiassa en välittänyt siitä lainkaan.')
    assert len(s) == 1
    assert s[0].replacements == ['Itse asiassa']


def test_more_joined_forms_flagged():
    for t, fix in (('Säästin rahaa vähänväliä koko vuoden.', 'vähän väliä'),
                   ('Hän maksoi kaupanpäälle vielä yhden leivän.',
                    'kaupan päälle'),
                   ('Luin lehden samantien aamulla.', 'saman tien')):
        s = hits(t)
        assert len(s) == 1, t
        assert s[0].replacements == [fix], t


def test_more_apart_forms_flagged():
    for t, fix in (('Asia selvisi jälki käteen vasta myöhemmin.',
                    'jälkikäteen'),
                   ('Kangas oli poikki päin raitoja.', 'poikkipäin')):
        s = hits(t)
        assert len(s) == 1, t
        assert s[0].replacements == [fix], t


def test_correct_forms_not_flagged():
    for t in ('Itse asiassa en välittänyt siitä lainkaan.',
              'Hän juoksi edestakaisin koko päivän.',
              'Säästin vähän väliä ja maksoin kaupan päälle.',
              'Luen lehteä koko ajan.'):
        assert hits(t) == [], t


def test_equal_variants_not_flagged():
    # ohjepankki sallii molemmat (~), joten ei liputeta kumpaakaan
    for t in ('Hän katsoi nurin päin.', 'Hän katsoi nurinpäin.',
              'Se on itsestäänselvä asia.', 'Pikkuhiljaa tultiin perille.',
              'Pikku hiljaa tultiin perille.'):
        assert hits(t) == [], t


def test_punctuation_between_blocks_join():
    assert hits('Hän ei edes, takaisin katsonut.') == []
    assert hits('Poikki, päin vastoin, kaikki meni.') == []


def test_edes_takaisin_and_nimen_omaan_are_ordinary_phrases():
    # "edes" (even) + "takaisin", "nimen" (genitive) + "omaan" are not the fossilized words
    from punakyna.pipeline import check_text
    for t in ('En saanut edes takaisin lainaamaani kirjaa.',
              'Laita nimen omaan kohtaan allekirjoitus.'):
        assert [s for s in check_text(t, use_spelling=False, use_gc=False)
                if s.rule == 'TYPO_SANAPARI'] == [], t


def test_all_caps_casing_preserved():
    s = hits('ITSEASIASSA EN VALITTANYT.')
    assert len(s) == 1
    assert s[0].replacements == ['ITSE ASIASSA']
