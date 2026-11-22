"""PUNCT_COMMA_MUTTA_VAAN: pilkku mutta/vaan-konjunktion edella, kun sen jalkeen
seuraa kokonainen paalause (ohjepankki, "Pilkku ja mutta, vaan")."""
from punakyna.pipeline import check_text


def hits(t):
    return [s for s in check_text(t, use_spelling=False)
            if s.rule == 'PUNCT_COMMA_MUTTA_VAAN']


def test_full_clause_after_mutta_vaan_is_flagged():
    for t in ('Mies tuli kotiin mutta nainen lähti töihin.',
              'Yritys ei vastaa vaan he ovat itse vastuussa.',
              'Hän ei ole vain väsynyt vaan hän on myös sairas.',
              'Sanoin sen mutta kukaan ei kuunnellut.',
              'Kauppa aukeaa mutta se tapahtuu vasta maanantaina.',
              'Sää selkeni mutta Anna tuli silti.'):
        r = hits(t)
        assert len(r) == 1, t
        assert r[0].replacements[0].startswith(', '), t


def test_non_clause_and_existing_comma_not_flagged():
    for t in ('Mies tuli kotiin, mutta nainen lähti töihin.',
              'Lääkärit hyväksyvät akupunktion mutta eivät ginsengjuurta.',
              'Pohjoisen naiset eivät nöyristele vaan haluavat huipulle.',
              'Hän on väsynyt mutta iloinen.',
              'Hän tuli mutta lähti heti.',
              'Hän tuli mutta ei jäänyt.',
              'Hidas mutta varma tie vie perille.',
              'Hän ei ole vain älykäs vaan myös ahkera.',
              'Mutta hän tuli sittenkin.',
              'Kaunis mutta vanha talo myytiin.',
              # subjekti ei heti mutta-sanan jalkeen: tarkkuusrajoitus
              'Arkisin salilla on hiljaista mutta viikonloppuisin siellä käy paljon.'):
        assert not hits(t), t
