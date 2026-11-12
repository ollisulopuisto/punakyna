"""GUI-tason Writer-testi (Xvfb): Todellinen Writer-istunto, ei vain headless.

Todistaa loppuun asti: .oxt asentuu profiiliin, komponentti on suomen
konfiguroitu proofreader KAYTTOLIITTYMAistunnossa, dokumentin teksti on
fi-FI, ja doProofreading palauttaa Punakynän säännön paikallisen API:n
kautta - kaikki samassa graafisessa Writer-prosessissa.

RAJOITUS (dokumentoitu): taustaoikoluvun sininen aaltoviiva EI piirry
tässä hiekkalaatikossa, koska profiilista puuttuu suomen
oikeinkirjoitustarkistin (hunspell/voikko-LO), jonka kautta LO:n
taustaprosessi käynnistää proofreaderit. Pikseliväite aaltoviivasta
jää tarkoituksella pois - Macilla suomen sanasto on yleensä olemassa,
mutta sitä ei ole varmistettu. Kuvakaappaus tallennetaan artefaktiksi.
"""
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
XVFB = shutil.which('Xvfb')
IMPORT = shutil.which('import')  # ImageMagick
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XPDIR = os.path.join(REPO, 'adapters', 'libreoffice', 'xproofreader')
API_PORT = 8377
UNO_PORT = 2002
DISPLAY = ':99'

try:
    subprocess.run(['/usr/bin/python3', '-c', 'import uno'],
                   check=True, capture_output=True)
    HAS_UNO = True
except Exception:
    HAS_UNO = False

pytestmark = pytest.mark.skipif(
    not (SOFFICE and os.path.exists(UNOPKG) and HAS_UNO and XVFB and IMPORT),
    reason='soffice/unopkg/python3-uno/Xvfb/import puuttuu')

FILL_DOC = r'''
import time, uno
from com.sun.star.lang import Locale
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext(
    'com.sun.star.bridge.UnoUrlResolver', local)
ctx = resolver.resolve(
    'uno:socket,host=127.0.0.1,port=PORTNO;urp;StarOffice.ComponentContext')
desktop = ctx.ServiceManager.createInstanceWithContext(
    'com.sun.star.frame.Desktop', ctx)
doc = None
for _ in range(120):
    doc = desktop.CurrentComponent
    if doc is not None:
        break
    time.sleep(0.5)
assert doc, 'ei nakyvaa dokumenttia'
cursor = doc.Text.createTextCursor()
cursor.CharLocale = Locale('fi', 'FI', '')
doc.Text.insertString(
    cursor,
    'Me olen likaisia.\nTämä on on testi.\nTämä lause on oikein.', False)
doc.CurrentController.Frame.ContainerWindow.toFront()
print('filled', len(doc.Text.getString()))
'''.replace('PORTNO', str(UNO_PORT))

DIAG = r'''
import uno
from com.sun.star.lang import Locale
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext(
    'com.sun.star.bridge.UnoUrlResolver', local)
ctx = resolver.resolve(
    'uno:socket,host=127.0.0.1,port=PORTNO;urp;StarOffice.ComponentContext')
smgr = ctx.ServiceManager
lmgr = smgr.createInstanceWithContext(
    'com.sun.star.linguistic2.LinguServiceManager', ctx)
loc = Locale('fi', 'FI', '')
svcs = lmgr.getConfiguredServices(
    'com.sun.star.linguistic2.Proofreader', loc)
print('CONFIGURED', list(svcs))
desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.CurrentComponent
c = doc.Text.createTextCursor()
c.gotoStart(False)
print('LOCALE', c.CharLocale.Language, c.CharLocale.Country)
xpr = smgr.createInstanceWithContext(
    'org.punakyna.comp.pyuno.PunakynaProofreader', ctx)
res = xpr.doProofreading(1, 'Me olen likaisia.', loc, 0, 18, ())
print('DIRECT', [(e.aRuleIdentifier, e.nErrorStart, e.nErrorLength)
                 for e in res.aErrors])
'''.replace('PORTNO', str(UNO_PORT))


def _wait_port(port, deadline):
    while time.time() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.5).close()
            return True
        except OSError:
            time.sleep(0.5)
    return False


def test_writer_gui_proofreader_end_to_end(tmp_path):
    load_or_create_token()
    load_or_create_app_token('libreoffice')
    api = make_server(port=API_PORT, tokens_provider=load_all_tokens)
    threading.Thread(target=api.serve_forever, daemon=True).start()

    oxt = str(tmp_path / 'punakyna-proofreader.oxt')
    subprocess.run([sys.executable, os.path.join(XPDIR, 'make_oxt.py'), oxt],
                   check=True, capture_output=True)
    profile_uri = 'file://' + str(tmp_path / 'louser')
    subprocess.run([UNOPKG, 'add', '-f', oxt,
                    f'-env:UserInstallation={profile_uri}'],
                   check=True, capture_output=True, timeout=120)

    xvfb = subprocess.Popen([XVFB, DISPLAY, '-screen', '0', '1280x1024x24'])
    time.sleep(2)
    env = dict(os.environ, DISPLAY=DISPLAY)
    soffice = subprocess.Popen(
        [SOFFICE, '--writer', '--norestore', '--nologo',
         f'--accept=socket,host=127.0.0.1,port={UNO_PORT};urp;'
         'StarOffice.ServiceManager',
         f'-env:UserInstallation={profile_uri}'],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fill = tmp_path / 'fill.py'
    diag = tmp_path / 'diag.py'
    fill.write_text(FILL_DOC)
    diag.write_text(DIAG)
    shot = tmp_path / 'writer.png'
    try:
        assert _wait_port(UNO_PORT, time.time() + 90), 'UNO-soketti ei avautunut'
        r = subprocess.run(['/usr/bin/python3', str(fill)],
                           capture_output=True, text=True, timeout=120, env=env)
        assert r.returncode == 0 and 'filled 57' in r.stdout, \
            r.stdout[-500:] + r.stderr[-1500:]
        time.sleep(12)
        d = subprocess.run(['/usr/bin/python3', str(diag)],
                           capture_output=True, text=True, timeout=120, env=env)
        assert d.returncode == 0, d.stderr[-1500:]
        out = d.stdout
        # GUI-istunnossa: komponentti on suomen konfiguroitu proofreader
        assert 'org.punakyna.comp.pyuno.PunakynaProofreader' in out, out
        # dokumentin teksti on suomea
        assert 'LOCALE fi FI' in out, out
        # doProofreading -> paikallinen API -> meidän sääntö, oikea span
        assert "'punakyna.PRON_VERB_AGREEMENT', 3, 4" in out, out
        # kuvakaappaus artefaktiksi (ei pikseliväitettä aaltoviivasta)
        subprocess.run([IMPORT, '-window', 'root', str(shot)],
                       check=True, env=env, capture_output=True, timeout=60)
        assert shot.exists() and shot.stat().st_size > 5000
    finally:
        soffice.terminate()
        try:
            soffice.wait(timeout=10)
        except subprocess.TimeoutExpired:
            soffice.kill()
        xvfb.terminate()
        api.shutdown(); api.server_close()
        revoke_app_token('libreoffice')
    assert not (TOKENS_DIR / 'libreoffice').exists()
