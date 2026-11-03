"""Offset-muunnokset: Python-koodipisteet vs UNO:n UTF-16-positiot.
Kriittinen ennen kuin sovitin korostaa tekstiä sovelluksessa."""
import sys
sys.path.insert(0, 'adapters/libreoffice')
from offsets import py_offset_to_uno


def test_ascii_same():
    s = 'Tämä on testi.'
    assert py_offset_to_uno(s, 7) == 7


def test_diacritics_same():
    # ä/ö ovat BMP:ssä: yksi UTF-16-yksikkö = yksi koodipiste
    s = 'Päälliköllä on äiti.'
    assert py_offset_to_uno(s, len(s)) == len(s)


def test_emoji_diverges():
    s = '😀 on on testi'  # emoji = 1 koodipiste, 2 UTF-16-yksikköä
    assert s.index('on') == 2
    assert py_offset_to_uno(s, 2) == 3  # UNO-positio = +1
    assert py_offset_to_uno(s, len(s)) == len(s) + 1


def test_multiple_emoji_accumulate():
    s = '😀x😀 on'
    i = s.index('on')
    assert py_offset_to_uno(s, i) == i + 2


def test_multiline_paragraph_offsets_stable():
    # rivinvaihto kappaleen sisällä: indeksit pysyvät samana
    s = 'eka rivi\ntoka on on rivi'
    i = s.index('on on')
    assert py_offset_to_uno(s, i) == i
    assert py_offset_to_uno(s, i + 5) == i + 5
