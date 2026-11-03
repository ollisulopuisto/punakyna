"""PRON_VERB_AGREEMENT: asemosana + viereinen finiittiverbi."""
from punakyna.pipeline import check_text


def rules(text):
    return [s.rule for s in check_text(text, use_spelling=False)]


def test_me_olen_flagged_with_olla_replacement():
    s = check_text('Me olen likaisia.', use_spelling=False)
    hit = [x for x in s if x.rule == 'PRON_VERB_AGREEMENT']
    assert len(hit) == 1
    assert hit[0].start == 3 and hit[0].end == 7
    assert hit[0].replacements == ['olemme']


def test_he_on_flagged():
    assert 'PRON_VERB_AGREEMENT' in rules('He on vanhoja.')


def test_colloquial_negatives_not_flagged():
    # puhekieli: me + passiivi, seka yksikko- etta monikko-predikatiivi
    assert 'PRON_VERB_AGREEMENT' not in rules('Me ollaan likainen.')
    assert 'PRON_VERB_AGREEMENT' not in rules('Me ollaan likaisia.')
    assert 'PRON_VERB_AGREEMENT' not in rules('Me mennään kauppaan.')
    assert 'PRON_VERB_AGREEMENT' not in rules('Me oltiin kotona.')
    # tuntemattomia puhekielimuotoja ei arvioida ("oon" ei sanastossa)
    assert 'PRON_VERB_AGREEMENT' not in rules('Mä oon täällä.')


def test_correct_standard_forms_not_flagged():
    for s in ('Minä olen likainen.', 'Sinä olet väärässä.',
              'Hän menee kouluun.', 'Me menimme kouluun.',
              'Te olette oikeassa.', 'He menevät ulos.',
              'Minä näen hänet.', 'Me emme menneet.'):
        assert 'PRON_VERB_AGREEMENT' not in rules(s), s


def test_nonadjacent_subject_left_alone():
    # etainen subjekti on jasennystason asia - saanto ei arvaile
    assert 'PRON_VERB_AGREEMENT' not in rules(
        'Minä ensimmäistä kertaa kunnolla näkee hänet.')
