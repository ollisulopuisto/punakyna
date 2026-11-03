"""Parser-taso TODELLA moottoripolussa (ajetaan parser-venv-aliprosessissa,
jossa stanza+libvoikko ovat). Skippaa jos parser-venv puuttuu."""
import os
import subprocess

import pytest

PARSER_PY = os.path.expanduser('~/parser-venv/bin/python')

pytestmark = pytest.mark.skipif(not os.path.exists(PARSER_PY),
                                reason='parser-venv puuttuu')

SCRIPT = r'''
import sys
from punakyna.pipeline import check_text
suggs = check_text('Minä ensimmäistä kertaa näkee hänet.', use_parser=True)
rules = sorted({s.rule for s in suggs})
print('RULES', rules)
for s in suggs:
    if s.rule.startswith(("PSV", "PNEG")):
        print('SPAN', s.rule, s.start, s.end, repr("Minä ensimmäistä kertaa näkee hänet."[s.start:s.end]))
suggs2 = check_text('Minä ensimmäistä kertaa näen hänet. Lapset juoksevat.', use_parser=True)
bad = [s.rule for s in suggs2 if s.rule.startswith(("PSV", "PNEG"))]
print('CLEAN', bad)
'''


def test_parser_tier_flags_and_offsets():
    proc = subprocess.run([PARSER_PY, '-c', SCRIPT], capture_output=True,
                          text=True, timeout=180, cwd='.')
    assert proc.returncode == 0, proc.stderr
    assert "PSV_PERSON" in proc.stdout, proc.stdout
    # offset osuu sanaan "näkee"
    assert "SPAN PSV_PERSON 24 29 'näkee'" in proc.stdout, proc.stdout
    assert 'CLEAN []' in proc.stdout, proc.stdout


SCRIPT_SERVER = r'''
import json, threading, urllib.request
from punakyna.api import make_server
srv = make_server(port=0)  # ei tunnusta: mittaus/vaittesti
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]
results, errors = [], []
def worker():
    try:
        for _ in range(2):
            body = json.dumps({"text": "Minä ensimmäistä kertaa näkee hänet.", "use_parser": True}).encode()
            req = urllib.request.Request(f"http://127.0.0.1:{port}/check", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                d = json.loads(resp.read())
                results.append((resp.status, any(s["rule"] == "PSV_PERSON" for s in d["suggestions"])))
    except Exception as e:
        errors.append(repr(e))
ts = [threading.Thread(target=worker) for _ in range(4)]
for t in ts: t.start()
for t in ts: t.join()
print("RESULTS", results)
print("ERRORS", errors)
# kokoraja: 20001 merkkiä -> 400
big = json.dumps({"text": "a " * 11000, "use_parser": True}).encode()
req = urllib.request.Request(f"http://127.0.0.1:{port}/check", data=big,
    headers={"Content-Type": "application/json"})
try:
    urllib.request.urlopen(req)
    print("BIG ok(odottamaton)")
except urllib.error.HTTPError as e:
    print("BIG", e.code)
'''


def test_parser_concurrent_optin_and_caps():
    proc = subprocess.run([PARSER_PY, '-c', SCRIPT_SERVER], capture_output=True,
                          text=True, timeout=300, cwd='.')
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.count('(200, True)') == 8, proc.stdout
    assert 'ERRORS []' in proc.stdout, proc.stdout
    assert 'BIG 400' in proc.stdout, proc.stdout


SCRIPT_MISSING_MODEL = r'''
import os, tempfile
os.environ["STANZA_RESOURCES_DIR"] = tempfile.mkdtemp()  # tyhjä: malli puuttuu
import punakyna.parser_tier as pt
pt._nlp = None
from punakyna.backend_voikko import get_voikko
try:
    pt.check("Minä näkee hänet.", voikko=get_voikko())
    print("EI VIRHETTÄ (odottamaton)")
except pt.ParserUnavailable as e:
    print("OK", "ei löydy paikallisesti" in str(e))
'''


def test_parser_missing_model_fails_clean():
    proc = subprocess.run([PARSER_PY, '-c', SCRIPT_MISSING_MODEL],
                          capture_output=True, text=True, timeout=180, cwd='.')
    assert proc.returncode == 0, proc.stderr
    assert 'OK True' in proc.stdout, proc.stdout + proc.stderr
