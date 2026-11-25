# -*- coding: utf-8 -*-
"""PUNCT_COMMA_LAUSEENVASTIKE: lauseenvastiketta ei eroteta pilkulla.

Lähde: ohjepankki, "Pilkku ja lauseenvastike: auringon noustua lähdimme"
(luettu 2026-11-25). Yleiskielen suositus: ei pilkkua alussa eikä lopussa;
poikkeus: vastikkeen jälkeen tuleva että-sivulause erotetaan pilkulla.
"""
from punakyna.pipeline import check_text


def _hits(text, rule='PUNCT_COMMA_LAUSEENVASTIKE'):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == rule]


def test_initial_vastike_with_possessive_comma_flagged():
    for t in ('Soitettuaan, hän hämmästyi.',
              'Luettuasi johdannon, vastaa kysymyksiin.',
              'Asetuttuaan Mikkeliin, taiteilija toimi opettajana.'):
        assert len(_hits(t)) == 1, t


def test_initial_a_infinitive_purpose_flagged():
    assert len(_hits('Voidaksemme vastata tarpeisiin, kehitämme '
                     'valikoimaa.')) == 1
    assert len(_hits('Kehittääkseen tuotetta, tiimi kokoontui.')) == 1


def test_genitive_subject_temporal_flagged():
    assert len(_hits('Auringon noustua, lähdimme matkaan.')) == 1
    assert len(_hits('Suomen kesän ollessa kauneimmillaan, on aika '
                     'miettiä lomamatkaa.')) == 1


def test_final_vastike_flagged():
    assert len(_hits('Mitä tukia opiskelija voi saada, muuttaessaan '
                     'pois kotoa?')) == 1
    assert len(_hits('Tuon tanssiin jotain omaani, lisäämällä omia '
                     'ideoitani.')) == 1


def test_ilman_rakenne_flagged():
    assert len(_hits('Ilman koulun tarjoamia oppeja, minulla ei olisi '
                     'mitään käsitystä Excelistä.')) == 1
    assert len(_hits('Hän teki sen, ilman apua.')) == 1


def test_no_comma_no_flag():
    for t in ('Soitettuaan keskuksen vanhaan numeroon soittaja '
              'hämmästyi.',
              'Auringon noustua lähdimme matkaan.',
              'Hän pyysi aina neuvoani uskoen.',
              'Ilman koulun tarjoamia oppeja minulla ei olisi mitään '
              'käsitystä Excelistä.'):
        assert not _hits(t), t


def test_comma_before_conjunction_after_vastike_allowed():
    # että-sivulause erotetaan pilkulla hallitsevasta verbistä (ohje)
    assert not _hits('Hän pyysi aina neuvoani uskoen, että voin auttaa.')
    # pilkku ennen ja-alkuista kokonaista päälausetta on pakollinen
    assert not _hits('Minä näin auringon noustua, ja se oli kaunis.')


def test_ilman_muuta_idiom_not_flagged():
    assert not _hits('Hän on, ilman muuta, oikeassa.')
    assert not _hits('Ilman muuta, hän on oikeassa.')


def test_ordinary_sentences_not_flagged():
    for t in ('Hän saapui kotiin, ja perhe oli iloinen.',
              'Ministeri totesi, että asia on loppuun käsitelty.',
              'Kesällä perhe kunnosti saunaa, ja talvella keittiön.'):
        assert not _hits(t), t


def test_ilman_etta_clause_and_list_commas_are_not_flagged():
    # "ilman että" aloittaa sivulauseen (pilkku kuuluu), ja luettelon pilkku
    # ilman-ilmauksen sisällä on luettelon pilkku.
    for t in ('Hän lähti, ilman että kukaan huomasi.',
              'Ilman ruokaa, vettä ja unta hän selvisi.',
              'Hän osti leipää, maitoa, ilman sokeria.'):
        assert not _hits(t), t
    assert len(_hits('Ilman koulun tarjoamia oppeja, minulla ei olisi '
                     'mitään käsitystä Excelistä.')) == 1
