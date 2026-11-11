"""Regression: clitic-bearing passive participles keep the warning.

"Minä olen mentykin kotiin" must still be flagged (Devin review on PR #45):
the suffix pre-filter discarded "mentykin" because it does not end in
tu/ty, so the previously emitted grammar warning disappeared. These tests
use a fake voikko so they run without libvoikko.
"""
from punakyna.rules import _Tok, check_active_perfect_passive_participle

_PASSIVE = {'CLASS': 'laatusana', 'PARTICIPLE': 'past_passive',
            'FSTOUTPUT': '[Xp]mennä[X]menty'}


class _FakeVoikko:
    """Vastaa kuin Voikko: passiivin TU-partisiipille analyysi, muuten []."""

    def __init__(self, participles):
        self.participles = set(participles)

    def analyze(self, word):
        if word.lower() in self.participles:
            return [dict(_PASSIVE)]
        return []


def _toks(sent):
    out, pos = [], 0
    for w in sent.split():
        start = sent.index(w, pos)
        out.append(_Tok(text=w, start=start, end=start + len(w), ttype=None))
        pos = start + len(w)
    return out


def _hits(sent, participles=('menty', 'mentykin')):
    return check_active_perfect_passive_participle(
        sent, 0, _toks(sent), _FakeVoikko(participles), {})


def test_clitic_bearing_participle_flagged():
    h = _hits('olen mentykin')
    assert len(h) == 1
    assert (h[0].start, h[0].end) == (5, 13)


def test_clitic_preserved_in_replacement():
    assert _hits('olen mentykin')[0].replacements == ['mennytkin']
    assert _hits('ovat mentykin')[0].replacements == ['menneetkin']


def test_bare_participle_still_flagged():
    assert _hits('olen menty')[0].replacements == ['mennyt']


def test_clitic_word_without_participle_analysis_not_flagged():
    # Liiteloppuinen sana ilman passiivipartisiippianalyysia ei liputeta.
    assert not _hits('olen mentykin', participles=())
    assert not _hits('olen talossakin')


def test_question_clitic_gets_no_one_word_replacement():
    # -ko/-kö kuuluu apuverbiin ("Olenko mennyt?"), ei partisiippiin:
    # yhden sanan korjaus "mennytkö" olisi epäkieliopillinen.
    h = _hits('olen mentykö', participles=('mentykö',))
    assert len(h) == 1
    assert h[0].replacements == []
    assert 'mennyt' in h[0].message
