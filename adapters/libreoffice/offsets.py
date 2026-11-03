"""Offset-muunnos Python-koodipisteiden ja UNO:n UTF-16-posiitojen välillä.

Ei UNO-riippuvuutta: testattava ilman LibreOfficea. Kriittinen ennen kuin
sovitin korostaa tekstiä sovelluksessa.
"""


def py_offset_to_uno(s, i):
    """Muunna Python-koodipisteindeksi UNO:n merkkipositioksi.

    LibreOfficen tekstipositiot ovat UTF-16-koodiyksiköitä: BMP:n
    ulkopuolinen merkki (esim. emoji) on UNO:ssa 2 yksikköä, Pythonissa 1.
    """
    return len(s[:i].encode('utf-16-le')) // 2
