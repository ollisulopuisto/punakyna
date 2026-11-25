# -*- coding: utf-8 -*-
"""PUNCT_COMMA_KUTEN: verbillinen kuten-jakso erotetaan pilkulla.

Lähde: ohjepankki, "Konjunktiot: kuten" (luettu 2026-11-25). Kun
'niin kuin' -merkityksinen kuten-jakso on lause (sisältää
persoonamuotoisen verbin), se erotetaan päälauseesta pilkulla;
'esimerkiksi'-merkityksinen jakso erotetaan aina. Verbitön jakso
("kuten aina", "kuten kuninkaalliset") ei saa pilkkua.
"""
from punakyna.pipeline import check_text


def _hits(text, rule='PUNCT_COMMA_KUTEN'):
    return [s for s in check_text(text, use_spelling=False, use_gc=False)
            if s.rule == rule]


def test_missing_comma_before_verbal_kuten_clause_flagged():
    for t in ('Säiliöt ovat erittäin huonossa kunnossa kuten kuvasta '
              'selvästi näkyykin.',
              'Nämä kaikki ovat hyviä asioita, mutta politiikkaan '
              'kaivataan muutakin kuten äänestäjät osoittivat.',
              'Täällä on mukavaa kuten voitte nähdäkin.'):
        r = _hits(t)
        assert len(r) == 1, t


def test_verbless_kuten_phrase_not_flagged():
    for t in ('Täällä on mukavaa kuten aina.',
              'Lomaile kuten kuninkaalliset.',
              'Hän selviytyi kokeesta kuten tavallisestikin.'):
        assert not _hits(t), t


def test_comma_already_present_not_flagged():
    for t in ('Säiliöt ovat huonossa kunnossa, kuten kuvasta näkyy.',
              'Myytävänä oli elintarvikkeita, kuten leipää, kahvia ja '
              'hedelmiä.',
              'Kuten EU:n ilmastopaketti osoittaa, energiankäytöllä on '
              'suuri vaikutus.'):
        assert not _hits(t), t
