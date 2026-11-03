import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from punakyna.pipeline import check_text  # noqa


def rules_for(text):
    return {s.rule for s in check_text(text, use_spelling=False)}


def test_negation_connegative():
    assert 'NEG_CONNEGATIVE' in rules_for('Minä en tienneet asiasta.')
    assert 'NEG_CONNEGATIVE' not in rules_for('Minä en tiennyt asiasta.')
    assert 'NEG_CONNEGATIVE' not in rules_for('Hän ei voi tulla.')
    assert 'NEG_CONNEGATIVE' not in rules_for('Hän ei ole tullut.')


def test_negation_number():
    assert 'NEG_NUMBER' in rules_for('He ei tule.')
    assert 'NEG_NUMBER' in rules_for('Me ei mennä.')
    assert 'NEG_NUMBER' not in rules_for('He eivät tule.')
    assert 'NEG_NUMBER' not in rules_for('Minä en mene.')


def test_olla_agreement():
    assert 'SV_AGREEMENT' in rules_for('Julkiset menot on kasvaneet.')
    assert 'SV_AGREEMENT' in rules_for('Kissat on pöydällä.')
    assert 'SV_AGREEMENT' not in rules_for('Kissat ovat pöydällä.')
    # eksistentiaalilause: verbi edeltaa monikollista subjektia
    assert 'SV_AGREEMENT' not in rules_for('Pöydällä on kirjat.')
    # monikon partitiivi ei ole nominatiivinen subjekti
    assert 'SV_AGREEMENT' not in rules_for('Menoja on leikattu.')


def test_double_word():
    assert 'DOUBLE_WORD' in rules_for('Tämä on on hyvä.')
    assert 'DOUBLE_WORD' not in rules_for('Tämä on hyvä.')


def test_cap_common_noun():
    assert 'CAP_COMMON_NOUN' in rules_for('Kokous pidetään Tammikuussa.')
    assert 'CAP_COMMON_NOUN' in rules_for('Tapaamme Maanantaina.')
    assert 'CAP_COMMON_NOUN' not in rules_for('Tammikuussa on kylmä.')
    assert 'CAP_COMMON_NOUN' not in rules_for('Kokous on maanantaina.')


def test_sentence_start():
    assert 'VOIKKO_GC' in rules_for('tämä alkaa pienellä.')
    assert 'VOIKKO_GC' not in rules_for('Tämä alkaa isolla.')


def test_spelling_layer():
    # aakkosellinen kirjoitusvirhe
    suggs = check_text('Hän asuu helsngissä.', use_rules=False)
    assert any(s.rule == 'SPELL' and 'helsingissä' in [r.lower() for r in s.replacements]
               for s in suggs)


def test_capitalized_unknown_word_is_info_not_error():
    # tarkkuus ensin: isoilla kirjoitettu tuntematon sana on yleensa nimi;
    # myos aakkosellisten kirjoitusvirheiden ehdotukset annetaan info-tasolla
    suggs = check_text('Hän asuu Helsingisä.', use_rules=False)
    assert any(s.rule == 'SPELL_UNKNOWN' and s.severity == 'info'
               and 'Helsingissä' in s.replacements for s in suggs)
    assert not any(s.rule == 'SPELL' for s in suggs)
    clean = check_text('Hän asuu Helsingissä.', use_rules=False)
    assert not [s for s in clean if s.rule == 'SPELL']


def test_voikko_gc_fixed_pair():
    suggs = check_text('Mies on joten kuten selvillä.', use_spelling=False)
    assert any(x.rule == 'VOIKKO_GC' and 'jotenkuten' in x.replacements for x in suggs)


def test_voikko_gc_proper_name_genitive():
    suggs = check_text('Avaimet löytyivät Reetan Taskun pohjalta.', use_spelling=False)
    assert any(x.rule == 'VOIKKO_GC' and x.replacements == ['taskun'] for x in suggs)


def test_fragment_not_flagged_for_terminal_punct():
    # AcceptUnfinishedParagraphsInGc=1: katkelmaa ei liputeta puuttuvasta
    # loppuvalimerkista (sama periaate kuin LibreOffice-integraatiossa)
    assert not rules_for('Tämä on lause')


def test_cap_common_noun_unknown_name_is_style_only():
    # 'Syksy' ei ole sanastossa erisnimena: sanakirjapohjainen tyokalu ei
    # voi tietaa sita sukunimeksi. Tarkkuuspolitiikka: tällaiset osumat
    # ovat aina korkeintaan style-tasoa, eivat koskaan error.
    suggs = check_text('Hänen sukunimensä on Syksy.', use_spelling=False)
    for x in suggs:
        if x.rule == 'CAP_COMMON_NOUN':
            assert x.severity == 'style'
            assert 'erisnimi' in x.message


def test_cap_common_noun_quoted_sentence_start_not_flagged():
    assert 'CAP_COMMON_NOUN' not in rules_for('Hän sanoi: "Tammikuussa on kylmä."')


def test_negation_conditional_connegative_not_flagged():
    assert 'NEG_CONNEGATIVE' not in rules_for('En haluaisi tulla.')


def test_necessiivirakenne_ei_osu():
    # VISK §1581: vakiosuomen rakenne, ei kongruenssivirhe
    assert 'SV_AGREEMENT' not in rules_for("Turvavyöt on pidettävä kiinnitettyinä koko lennon ajan.")
    assert 'SV_AGREEMENT' not in rules_for("Avaimet on palautettava klo 12:een mennessä.")
    assert 'SV_AGREEMENT' not in rules_for("Tällaiset valvontatiedot on asetettava saataville.")


def test_passiivin_perfekti_ei_osu():
    assert 'SV_AGREEMENT' not in rules_for("Näyttelijät on laitettu huutamaan.")
    assert 'SV_AGREEMENT' not in rules_for("Kaikki vaatteet on valmistettu ympäristöä säästäen.")


def test_kopula_adjektiivin_kanssa_osuu_edelleen():
    assert 'SV_AGREEMENT' in rules_for("Sen kädet on auki.")


def test_sv_agreement_multiword_proper_name():
    """Kollektiivierisnimi lauseen keskella: yksikkokongruenssi OK."""
    from punakyna.pipeline import check_text
    rs = check_text('Helsingin Sanomat on tässä asiassa varovainen.')
    assert not any(s.rule == 'SV_AGREEMENT' for s in rs)
