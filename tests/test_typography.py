"""TYPO_*: ohjepankin typografiasäännöt (prosentti, raha, kellonaika, lyhenteet)."""
from punakyna.pipeline import check_text


def hits(t, rule):
    return [s for s in check_text(t, use_spelling=False) if s.rule == rule]


def test_percent_and_currency():
    assert len(hits('Hinta nousi 10% vuodessa.', 'TYPO_PERCENT_SPACE')) == 1
    assert len(hits('Tilaa nyt, saat 25%:n alennuksen.', 'TYPO_PERCENT_SPACE')) == 1
    assert len(hits('Se maksaa 29,90€ per kuukausi.', 'TYPO_CURRENCY_SPACE')) == 1
    for t in ('Hinta nousi 10 % vuodessa.', 'Saat 25 %:n alennuksen.',
              'Se maksaa 29,90 € per kuukausi.', 'Osoite on a.fi/x%20y.',
              'Prosentti (%) on merkki.', 'Hän sai 100 prosenttia.'):
        assert not hits(t, 'TYPO_PERCENT_SPACE') and not hits(t, 'TYPO_CURRENCY_SPACE'), t


def test_clock_format_is_style_only():
    r = hits('Kokous alkaa klo 9:15 huomenna.', 'TYPO_CLOCK_FORMAT')
    assert len(r) == 1 and r[0].severity == 'style'
    assert len(hits('Kokous alkaa klo 09.15.', 'TYPO_CLOCK_FORMAT')) == 1
    for t in ('Kokous alkaa klo 9.15 huomenna.', 'Liike on auki kello 12–21.',
              'Kello 24.00 on keskiyö.', 'Suhde on 3:1.', 'Juna lähtee kello 0.05.'):
        assert not hits(t, 'TYPO_CLOCK_FORMAT'), t


def test_abbreviation_dot():
    for t in ('Mukaan tulivat esim Suomi ja Viro.', 'Kirjat, levyt jne ovat hyllyssä.',
              'Ota lamppu tms mukaan.'):
        assert len(hits(t, 'TYPO_ABBR_DOT')) == 1, t
    for t in ('Mukaan tulivat esim. Suomi ja Viro.', 'Kirjat, levyt jne. ovat hyllyssä.',
              'Ota lamppu tms. mukaan.', 'Esimerkki on selvä.', 'Osoite on esim.fi.'):
        assert not hits(t, 'TYPO_ABBR_DOT'), t


def test_decimal_point():
    for t, fix in (('Vesi oli 14.6 °C aamulla.', '14,6'), ('Litra maksaa 5.50 euroa.', '5,50'),
                   ('Paketti painaa 2.5 kg.', '2,5'), ('Nousu oli 3.2 %.', '3,2'),
                   ('Matka on 3.5 km.', '3,5')):
        r = hits(t, 'TYPO_DECIMAL_POINT')
        assert len(r) == 1 and r[0].replacements == [fix], t
    for t in ('Vesi oli 14,6 °C aamulla.', 'Kokous on 1.4. kello 9.30.', 'Kokous alkaa klo 9.15 huomenna.',
              'Katso kohta 2.1 ohjeesta.', 'Versio 1.2.3 on ulkona.', 'Osoite on 10.0.0.1 m.fi.',
              'Se maksaa 1.000 euroa.', 'Hän syntyi 3.5.1980 kg.', 'Suurpujottelun voittoaika oli 2.19,03.',
              'Juhla on 12.5. kello 18.', 'Tiedosto v2.5 kg.fi on pieni.'):
        assert not hits(t, 'TYPO_DECIMAL_POINT'), t


def test_range_hyphen():
    for t, fix in (('Liike on auki kello 9-12.', '9–12'),
                   ('Joukkueessa on 20-30 pelaajaa.', '20–30'),
                   ('Hän työskenteli vuosina 1853-1862.', '1853–1862'),
                   ('Ottelu päättyi 2-1.', '2–1'),
                   ('Lue sivut 5-8 ensin.', '5–8')):
        r = hits(t, 'TYPO_RANGE_HYPHEN')
        assert len(r) == 1 and r[0].replacements == [fix], t
    for t in ('Liike on auki kello 9–12.', 'Joukkueessa on 20–30 pelaajaa.',
              'Kone on Boeing 737-800.', 'Merkistö on UTF-8.',
              'Päiväys on 2026-11-08.', 'Aikaleima 2026-11-08 12:30.',
              'Tuotekoodi AB-123-CD kelpaa.', 'ISBN 978-951-123-456-7.',
              'Katso kohta 2.1 ohjeesta.', 'Versio 1.2.3 on ulkona.',
              'Kone on Boeing 737-800 ja 737-700.', 'Moottori on CFM International 56-3.',
              'Lehden ISSN 0355-2047 näkyy kannessa.', 'Sarjan ISSN 1798-2014.',
              'Tiedosto on Sääntökirja%202021-2022%20v2.pdf.'):
        assert not hits(t, 'TYPO_RANGE_HYPHEN'), t
