# -*- coding: utf-8 -*-
"""PUNCT_COMMA_LIST_JA: luettelon viimeisen osan ja/sekä/tai ilman pilkkua.

Lähde: ohjepankki, "Pilkku rinnasteisten lauseenjäsenten ja luettelon osien
välissä" (luettu 2026-11-25): "Maija, Matti ja muut" -malli; kahden viimeisen
osan välissä ja-sana ilman pilkkua.
"""
from punakyna.pipeline import check_text


def _hits(text, rule='PUNCT_COMMA_LIST_JA'):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == rule]


def test_comma_before_final_ja_in_list_flagged():
    for t in ('He lukivat Kiveä, Saarikoskea, Kilpeä, Hassista, ja muita '
              'suomalaisia kirjailijoita.',
              'Ostin maitoa, leipää, ja juustoa.',
              'Hän on älykäs, ahkera, ja rehellinen.'):
        r = _hits(t)
        assert len(r) == 1, t


def test_comma_before_seka_and_tai_in_list_flagged():
    assert len(_hits('Retkellä tarvitaan makuupussi, pyyhe, sekä '
                     'eväät.')) == 1
    assert len(_hits('Juotko kahvia, teetä, tai kaakaota?')) == 1


def test_correct_lists_not_flagged():
    for t in ('He lukivat Kiveä, Saarikoskea, Kilpeä, Hassista ja muita '
              'suomalaisia kirjailijoita.',
              'Ostin maitoa, leipää ja juustoa.',
              'Maija ja Matti tulivat käymään.'):
        assert not _hits(t), t


def test_two_item_conjunction_not_flagged():
    # ei aiempaa pilkkua: konjunktiopari, ei luettelo
    assert not _hits('Hän tuli, ja hän lähti.')
    assert not _hits('Ostin maitoa, ja leipää.')


def test_clause_chain_not_flagged():
    # aarellisverbi edellisen pilkun ja konjunktion välissä
    assert not _hits('Pihassa kaatui puita, katto irtosi tuulessa, ja '
                     'kulmakunta on ilman sähköä.')
    assert not _hits('Ministeri sanoi, että asia selvitetään, ja että '
                     'tulokset julkaistaan huomenna.')


def test_existential_tail_and_kuten_apposition_not_flagged():
    # eksistentiaalilause konjunktion jalkeen: pilkku pakollinen
    assert not _hits('Alueella oli oma kieli, uskonto ja lainsaadanto, '
                     'ja silla oli oma hallinto.')
    # kuten-tarkennuksen sulkeva pilkku ei ole luettelon osan erotin
    assert not _hits('MySQL tukee muistitietokantoja kuten Memcached ja '
                     'Redis, seka useita muita jarjestelmia.')


def test_nominative_and_finite_verb_after_ja_not_flagged():
    # ja-sanan jälkeen nominatiivi + aarellisverbi -> kokonainen lause
    assert not _hits('Helsinki, Tampere, ja Turku ovat suuria '
                     'kaupunkeja.')
    assert not _hits('Kahvi, tee, ja Matti joi kaakaota.')
