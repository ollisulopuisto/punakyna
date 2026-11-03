"""PRED_NUM: predikatiivin lukukongruenssi (VISK §1284, §1284 Huom., §1285).

Normi: monikollinen subjekti vaatii monikollisen predikatiivin - myös
puhekielessa, kun verbin kongruenssi lipsuu ("Nää kriminaalit oli
ääritapauksia"). Yksipersoonaisen passiivin predikatiivi on monikossa
("Onko täällä oltu kilttejä?"), joten me-passiivin yksiköllinen
nominatiivipredikatiivi ("Me ollaan likainen.") ei ole normin mukainen.
Poikkeukset: kollektiivierisnimet ("Helsingin Sanomat on varovainen",
§1284c), numeraalisubjektit (§1285).

Ajetaan parser-venv-aliprosessissa (stanza+libvoikko), kuten
test_parser_tier_engine.py.
"""
import os
import subprocess

import pytest

PARSER_PY = os.path.expanduser('~/parser-venv/bin/python')

pytestmark = pytest.mark.skipif(not os.path.exists(PARSER_PY),
                                reason='parser-venv puuttuu')

SCRIPT = r'''
from punakyna.pipeline import check_text


def rules(text):
    return sorted({s.rule for s in check_text(text, use_parser=True)})


flagged = ['Me ollaan likainen.', 'Autot ovat punainen.', 'He ovat vanha.']
pperf_flagged = [
    'Kilpailuun on osallistuneet tänä vuonna yhteensä seitsemäntoista kilpailijaa.',
    'Tulitusta oli kokoontuneet niskat kenossa pällistelemään muutama tuhat ihmistä.',
    'Lasku on vaikuttaneet hintoihin.',
]
pperf_clean = [
    'Kilpailuun on osallistunut tänä vuonna yhteensä seitsemäntoista kilpailijaa.',
    'Hän on tullut kotiin.',
    'He ovat tulleet kotiin.',
    'Me ollaan tultu kotiin.',
    'Me ollaan tulleet kotiin.',
    'Lasku on vaikuttanut hintoihin.',
    'Pojat ovat nähneet sen.',
]
for t in pperf_flagged:
    if 'PPERF_NUM' not in rules(t):
        fails.append('PPERF NOT FLAGGED: ' + t)
for t in pperf_clean:
    if 'PPERF_NUM' in rules(t):
        fails.append('PPERF FALSE POSITIVE: ' + t)
clean = [
    'Me ollaan likaisia.',
    'Autot ovat punaiset.',
    'Autot ovat punaisia.',
    'He ovat vanhoja.',
    'Hän on vanha.',
    'Lumi on puhdasta.',
    'Ne on ihan siistin kuuloset.',
    'Pojat ovat kilttejä.',
    'Häät olivat juhlalliset.',
    'Helsingin Sanomat on tässä asiassa varovainen.',
    'Kaksi heistä oli suomalaisia.',
    'Onko täällä oltu kilttejä?',
]
fails = []
for t in flagged:
    if 'PRED_NUM' not in rules(t):
        fails.append('NOT FLAGGED: ' + t)
for t in clean:
    if 'PRED_NUM' in rules(t):
        fails.append('FALSE POSITIVE: ' + t)
assert not fails, '; '.join(fails)
print('PRED_NUM CASES OK')
'''


def test_pred_num_cases():
    env = dict(os.environ)
    env['PYTHONPATH'] = os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))
    r = subprocess.run([PARSER_PY, '-c', SCRIPT], capture_output=True,
                       text=True, timeout=300, env=env)
    assert r.returncode == 0, r.stderr[-2000:]
    assert 'PRED_NUM CASES OK' in r.stdout


def test_pred_num_off_without_parser():
    from punakyna.pipeline import check_text
    assert not any(s.rule == 'PRED_NUM'
                   for s in check_text('Me ollaan likainen.',
                                       use_parser=False))
