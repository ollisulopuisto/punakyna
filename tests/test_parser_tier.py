"""Parser-tason moottoriintegraatio: opt-in, puuttuessa selkeä virhe."""
import pytest


def test_parser_tier_off_by_default():
    from punakyna.pipeline import check_text
    # persoonavirhe ilman parser-tasoa: ei PSV/PNEG-löydöksiä
    suggs = check_text('Minä näkee hänet.', use_parser=False)
    assert not any(s.rule.startswith(('PSV', 'PNEG')) for s in suggs)


def test_parser_optin_unavailable_message():
    stanza = pytest.importorskip  # jos stanza puuttuu: odotetaan ParserUnavailable
    try:
        import stanza  # noqa
        pytest.skip('stanza asennettu tähän venviin - virhepolku testattu parser-venv:ssä')
    except ImportError:
        pass
    from punakyna.parser_tier import check, ParserUnavailable
    from punakyna.backend_voikko import get_voikko
    with pytest.raises(ParserUnavailable) as e:
        check('Minä näkee hänet.', voikko=get_voikko())
    assert 'stanza ei asennettu' in str(e.value)
