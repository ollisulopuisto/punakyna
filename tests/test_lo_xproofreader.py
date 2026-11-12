"""TODELLINEN LibreOffice XProofreader -end-to-end (headless, tilapäisprofiili).

Ketju: rakennetaan .oxt -> unopkg add KERTAKÄYTTÖISEEN LO-profiiliin
(tmp_path; käyttäjän oikeaan LibreOffice-profiiliin ei kosketa) ->
käynnistetään soffice --headless UNO-soketilla -> python-uno -skripti
kysyy LinguServiceManagerin konfiguroidut suomen proofreaderit (meidän
komponentti pitää löytyä rekisteröinnistä) ja kutsuu doProofreadingiä
-> virheet palautuvat oikeilla UTF-16-sijainneilla paikalliselta
Punakynä-API:lta sovelluskohtaisella 'libreoffice'-tunnuksella.

Ympäristön palautus: profiili on tmp_pathissa, sovellustunnus
perutaan finally-lohkossa, soffice tapetaan. Skippaa jos soffice/unopkg
tai /usr/bin/python3:n uno puuttuu.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time

import pytest

from punakyna.api import make_server
from punakyna.tokenfile import (
    load_or_create_token, load_or_create_app_token, load_all_tokens,
    revoke_app_token, TOKENS_DIR)

SOFFICE = shutil.which('soffice') or shutil.which('libreoffice')
UNOPKG = shutil.which('unopkg') or '/usr/lib/libreoffice/program/unopkg'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XPDIR = os.path.join(REPO, 'adapters', 'libreoffice', 'xproofreader')
API_PORT = 8377
UNO_PORT = 2002
APP = 'libreoffice'

try:
    subprocess.run(['/usr/bin/python3', '-c', 'import uno'],
                   check=True, capture_output=True)
    HAS_UNO = True
except Exception:
    HAS_UNO = False

pytestmark = pytest.mark.skipif(
    not (SOFFICE and os.path.exists(UNOPKG) and HAS_UNO),
    reason='LibreOffice/unopkg/python3-uno puuttuu')

UNO_SCRIPT = r'''
import json, uno
from com.sun.star.lang import Locale

local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", local)
ctx = resolver.resolve(
    "uno:socket,host=127.0.0.1,port=PORTNO;urp;StarOffice.ComponentContext")
smgr = ctx.ServiceManager
lmgr = smgr.createInstanceWithContext(
    "com.sun.star.linguistic2.LinguServiceManager", ctx)
loc = Locale("fi", "FI", "")
svcs = lmgr.getConfiguredServices(
    "com.sun.star.linguistic2.Proofreader", loc)
out = {"services": list(svcs)}
xpr = smgr.createInstanceWithContext(
    "org.punakyna.comp.pyuno.PunakynaProofreader", ctx)

def utf16_len(s):
    return len(s.encode("utf-16-le")) // 2

def run(text):
    res = xpr.doProofreading(1, text, loc, 0, utf16_len(text), ())
    return [{"rule": e.aRuleIdentifier, "start": e.nErrorStart,
             "len": e.nErrorLength, "msg": e.aFullComment}
            for e in res.aErrors]

out["plain"] = run("Tämä on on testi.")
out["emoji"] = run("😀 Tämä on on testi.")
out["clean"] = run("Tämä on testi.")
print("RESULT_JSON:" + json.dumps(out))
'''.replace('PORTNO', str(UNO_PORT))


def _wait_port(port, deadline):
    while time.time() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.5).close()
            return True
        except OSError:
            time.sleep(0.5)
    return False


def test_xproofreader_headless_end_to_end(tmp_path):
    load_or_create_token()
    load_or_create_app_token(APP)
    api = make_server(port=API_PORT, tokens_provider=load_all_tokens)
    threading.Thread(target=api.serve_forever, daemon=True).start()

    profile = tmp_path / 'louser'
    profile_uri = 'file://' + str(profile)
    oxt = str(tmp_path / 'punakyna-proofreader.oxt')
    subprocess.run([sys.executable,
                    os.path.join(XPDIR, 'make_oxt.py'), oxt],
                   check=True, capture_output=True)
    r = subprocess.run([UNOPKG, 'add', '-f', oxt,
                        f'-env:UserInstallation={profile_uri}'],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (
        f'unopkg add epaonnistui ({r.returncode}):\nstdout: {r.stdout}\n'
        f'stderr: {r.stderr}')

    soffice = subprocess.Popen(
        [SOFFICE, '--headless', '--norestore', '--nologo',
         f'--accept=socket,host=127.0.0.1,port={UNO_PORT};urp;'
         'StarOffice.ServiceManager',
         f'-env:UserInstallation={profile_uri}'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    script = tmp_path / 'uno_check.py'
    script.write_text(UNO_SCRIPT)
    try:
        assert _wait_port(UNO_PORT, time.time() + 60), 'UNO-soketti ei avautunut'
        r = subprocess.run(['/usr/bin/python3', str(script)],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-2000:]
        line = [l for l in r.stdout.splitlines()
                if l.startswith('RESULT_JSON:')]
        assert line, r.stdout[-2000:]
        res = json.loads(line[0][len('RESULT_JSON:'):])

        # Rekisteröinti näkyy LinguServiceManagerissa suomen proofreaderina.
        assert any('Punakyna' in s for s in res['services']), res['services']

        # "Tämä on on testi.": toinen 'on' alkaa kohdasta 8, pituus 2
        # (BMP-teksti: UTF-16 == koodipisteet).
        plain = [e for e in res['plain'] if e['rule'] == 'punakyna.DOUBLE_WORD']
        assert plain and plain[0]['start'] == 8 and plain[0]['len'] == 2, \
            res['plain']
        assert plain[0]['msg'], 'virheilmoituksen teksti puuttuu'

        # Emoji (2 UTF-16-yksikköä): toinen 'on' UTF-16-kohdassa 11,
        # vaikka koodipisteindeksi on 10 - muunnos toimii.
        emoji = [e for e in res['emoji'] if e['rule'] == 'punakyna.DOUBLE_WORD']
        assert emoji and emoji[0]['start'] == 11, res['emoji']

        # Puhdas virke: ei virheitä.
        assert res['clean'] == [], res['clean']
    finally:
        soffice.terminate()
        try:
            soffice.wait(timeout=15)
        except subprocess.TimeoutExpired:
            soffice.kill()
        api.shutdown(); api.server_close()
        revoke_app_token(APP)
    assert not (TOKENS_DIR / APP).exists()
