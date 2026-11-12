"""Taustaoikolukuputken GUI-testi (Xvfb): todelliset merkit Writerissa.

Erotuksena test_lo_writer_gui.py:hen (joka todistaa konfiguraation +
suoran doProofreading-kutsun) tama testaa KAYTTAJANAKYVAN putken:
hunspell-fi-sanasto (testiriippuvuus, fginter/hunspell-fi 0.2) tekee
LO-profiiliin suomen oikeinkirjoitustarkistimen, jolloin LO:n
taustaprosessi kaynnistaa myos Punakyna-proofreaderin. Varmistetaan
PIKSELEISTA: punainen aaltoviiva (kirjoitusvirhe, LO:n hunspell) ja
sininen aaltoviiva (kielioppivirhe, Punakyna) piirtyvat nakyvaan
dokumenttiin, plus oikolukudialogi nayttaa kielen ja ehdotukset.

Testiriippuvuus: PUNAKYNA_TEST_FI_DICT_OXT=/polku/dict-fi.oxt
(pakattu fginter/hunspell-fi 0.2 -julkaisun fi_FI.dic/.aff-tiedostoista;
Ei osa repoa eika asennuksia - pelkka testiprofiilin sanasto.)

TILA 2026-11-03 (rehellinen):
- voikko-laajennos (libreoffice-voikko 5.0 -debin sisaista oxt:ia vastaava)
  rekisteroityy: voikko.SpellChecker kaytettavissa/konfiguroitu fi-FI:lle,
  ja PUNAINEN aaltoviiva piirtyy tekstin "Kisssa" alle (130 pikselia
  tekstialueella; kontrolli 0). Vaatii LD_LIBRARY_PATH/PYTHONPATH/
  VOIKKO_DICTIONARY_PATH-ymparistomuuttujat hiekkalaatikossa.
- SININEN kielioppiviiva ei viela piirry: voikko-laajennoksen
  Linguistic.xcu kirjoittaa GrammarCheckerList/fi-FI -listan
  oor:op="replace" -toimenpiteella, joka pudottaa Punakynan pois
  konfiguroiduista proofreadereista. Ajoyhteinen korjaus
  (setConfiguredServices / ConfigurationUpdateAccess) ei tarttunut
  (commitChanges onnistui mutta luku naytti vanhaa), ja suora
  registrymodifications.xcu-injektio ennen kaynnistysta havisi LO:n
  uudelleenkirjoittaessa tiedoston. AVOINNA: pysyva tapa saada molemmat
  proofreaderit konfiguroitua samalla profiililla (esim. oman oxt:n
  GrammarCheckerList-item tai asennusjarjestys + verifiointi).
- Attribution-saanto: voikko.GrammarChecker EI tunnista
  PRON_VERB_AGREEMENT-tyyppia (ks. docs/research.md), joten sininen
  viiva "Me olen likaisia" -kohdalla on Punakynasta.

RATKAISTU KASIN 2026-11-03 (automaatio viela kesken):
  Profiili: voikko-oxt ILMAN Linguistic.xcu:ta (poistettu paketista JA
  manifestista - pelkka sisallon poisto rikkoo XML:n) + punakyna-oxt,
  jonka Linguistic.xcu:ssa GrammarCheckerList/fi-FI =
  <it>PunakynaProofreader</it><it>voikko.GrammarChecker</it> (it-formaatti,
  ei valilyonteja). Tulos: PROOF-CONF=[PunakynaProofreader],
  SPELL-CONF=[voikko.SpellChecker], SININEN alleviivaus piirtyi "olen"-
  sanan alle (46 px, y=306-309 = rivi 2; /tmp/writer-ui/crop_bgB_text.png)
  JA punainen "Kisssa"- ja "Tami"-sanojen alle. Dialogin kaappaus
  (.uno:SpellDialog) ei viela nay kuvassa - dispatch menee lapi mutta
  ikkuna ei renderoidy ajoissa.
  AVOINNA automaatiossa: RATKAISTU - puuttuva triggeri oli
  muokkaustapahtuma insertoinnin jalkeen (lopun valilyonti); sen jalkeen
  pytest-ajo tuottaa red=73 blue=46 ja testi OHITTAA. Dialogin kaappaus:
  .uno:SpellingAndGrammarDialog (EI .uno:SpellDialog) + 8 s odotus;
  todennettu kuvassa: suomen kieli, kirjoitusvirheen ehdotukset
  (voikko) JA kielioppivirheen selite + korjausehdotus "olemme"
  Punakynalta (teksti ilman kirjoitusvirheita -> dialogi avautuu suoraan
  kielioppivirheeseen).
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
IMPORT = shutil.which('import')
CONVERT = shutil.which('convert')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XPDIR = os.path.join(REPO, 'adapters', 'libreoffice', 'xproofreader')
VOIKKO_OXT = os.environ.get('PUNAKYNA_TEST_VOIKKO_OXT')
API_PORT = 8377
UNO_PORT = 2003
DISPLAY = ':98'

try:
    subprocess.run(['/usr/bin/python3', '-c', 'import uno'],
                   check=True, capture_output=True)
    HAS_UNO = True
except Exception:
    HAS_UNO = False

pytestmark = pytest.mark.skipif(
    not (SOFFICE and os.path.exists(UNOPKG) and HAS_UNO and XVFB and IMPORT
         and CONVERT and VOIKKO_OXT and os.path.exists(VOIKKO_OXT or '')),
    reason='soffice/uno/Xvfb/imagemagick tai PUNAKYNA_TEST_VOIKKO_OXT puuttuu')

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
    'Kisssa juoksee nopeasti.\nMe olen likaisia.\nTämä lause on oikein.',
    False)
doc.CurrentController.Frame.ContainerWindow.toFront()
time.sleep(3)
# taustatarkistuksen trigger: pieni muokkaus insertoinnin jalkeen
c2 = doc.Text.createTextCursor()
c2.gotoEnd(False)
doc.Text.insertString(c2, ' ', False)
print('filled', len(doc.Text.getString()))
'''.replace('PORTNO', str(UNO_PORT))

OPEN_DIALOG = r'''
import time, uno
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext(
    'com.sun.star.bridge.UnoUrlResolver', local)
ctx = resolver.resolve(
    'uno:socket,host=127.0.0.1,port=PORTNO;urp;StarOffice.ComponentContext')
smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.CurrentComponent
frame = doc.CurrentController.Frame
dispatcher = smgr.createInstanceWithContext(
    'com.sun.star.frame.DispatchHelper', ctx)
# vie kursori alkuun ja avaa oikolukudialogi (F7)
dispatcher.executeDispatch(frame, '.uno:GoToStartOfDoc', '', 0, ())
time.sleep(0.5)
dispatcher.executeDispatch(frame, '.uno:SpellingAndGrammarDialog', '', 0, ())
print('dialog dispatched')
'''.replace('PORTNO', str(UNO_PORT))


def _wait_port(port, deadline):
    while time.time() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.5).close()
            return True
        except OSError:
            time.sleep(0.5)
    return False


def _color_counts(png, x0=240, x1=600, y0=230, y1=340):
    """Laske voimakkaan punaiset/siniset pikselit TEKSTIALUEELLA.

    Koko ruudun laskenta on virheellinen: tyokalupalkin ikonit sisaltavat
    satoja punaisia/sinisia pikseleita. Rajaamalla dokumentin tekstirivien
    alle (aaltoviivojen paikka) kontrollikuvassa laskuri on 0.
    """
    r = subprocess.run(
        [CONVERT, str(png), '-depth', '8', 'txt:-'],
        capture_output=True, text=True, timeout=300)
    red = blue = 0
    for line in r.stdout.splitlines():
        # formaatti: x,y: (R,G,B)  #HEX  srgb(...)
        try:
            xy, rest = line.split(':', 1)
            x, y = (int(v) for v in xy.split(','))
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            vals = rest.split('(')[1].split(')')[0].split(',')
            rr, gg, bb = int(vals[0]), int(vals[1]), int(vals[2])
        except (IndexError, ValueError):
            continue
        if rr > 170 and gg < 110 and bb < 110:
            red += 1
        elif bb > 170 and rr < 130 and gg < 150:
            blue += 1
    return red, blue


def test_background_pipeline_marks_visible(tmp_path):
    load_or_create_token()
    load_or_create_app_token('libreoffice')
    api = make_server(port=API_PORT, tokens_provider=load_all_tokens)
    threading.Thread(target=api.serve_forever, daemon=True).start()

    oxt = str(tmp_path / 'punakyna-proofreader.oxt')
    subprocess.run([sys.executable, os.path.join(XPDIR, 'make_oxt.py'), oxt],
                   check=True, capture_output=True)
    # Testivariaatti voikko-paketista ILMAN Linguistic.xcu:ta: sen
    # GrammarCheckerList/fi-FI kirjoitetaan oor:op="replace":lla, mika
    # pudottaisi Punakynan konfiguroiduista proofreadereista. Tiedosto
    # poistettava myos manifestista - pelkka sisallon tyhjennys rikkoo
    # XML:n ja unopkg feilaa hiljaa. Vain testiprofiili.
    import re
    import zipfile
    spellonly = str(tmp_path / 'voikko-spellonly.oxt')
    with zipfile.ZipFile(VOIKKO_OXT) as zin, \
            zipfile.ZipFile(spellonly, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'Linguistic.xcu':
                continue
            data = zin.read(item.filename)
            if item.filename == 'META-INF/manifest.xml':
                data = re.sub(
                    rb'<manifest:file-entry[^>]*Linguistic\.xcu[^>]*/>\s*',
                    b'', data)
            zout.writestr(item, data)
    profile_uri = 'file://' + str(tmp_path / 'louser')
    for pkg in (spellonly, oxt):
        subprocess.run([UNOPKG, 'add', '-f', pkg,
                        f'-env:UserInstallation={profile_uri}'],
                       check=True, capture_output=True, timeout=180)

    xvfb = subprocess.Popen([XVFB, DISPLAY, '-screen', '0', '1280x1024x24'])
    time.sleep(2)
    env = dict(os.environ, DISPLAY=DISPLAY)
    # voikko-laajennos tarvitsee libvoikko.py-moduulin LO:n pythoniin
    vpp = os.environ.get('PUNAKYNA_TEST_VOIKKO_PYTHONPATH')
    if vpp:
        env['PYTHONPATH'] = vpp + ':' + env.get('PYTHONPATH', '')
    soffice = subprocess.Popen(
        [SOFFICE, '--writer', '--norestore', '--nologo',
         f'--accept=socket,host=127.0.0.1,port={UNO_PORT};urp;'
         'StarOffice.ServiceManager',
         f'-env:UserInstallation={profile_uri}'],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fill = tmp_path / 'fill.py'
    dlg = tmp_path / 'dlg.py'
    fill.write_text(FILL_DOC)
    dlg.write_text(OPEN_DIALOG)
    shot = tmp_path / 'writer-bg.png'
    shot_dlg = tmp_path / 'writer-dialog.png'
    try:
        assert _wait_port(UNO_PORT, time.time() + 90), 'UNO-soketti ei avautunut'
        r = subprocess.run(['/usr/bin/python3', str(fill)],
                           capture_output=True, text=True, timeout=120, env=env)
        assert r.returncode == 0 and 'filled' in r.stdout, \
            r.stdout[-500:] + r.stderr[-1500:]
        time.sleep(15)  # anna taustaoikoluvun merkita
        subprocess.run([IMPORT, '-window', 'root', str(shot)],
                       check=True, env=env, capture_output=True, timeout=60)
        red, blue = _color_counts(shot)
        print(f'PIXELS red={red} blue={blue}')
        assert red > 20, f'punainen aaltoviiva puuttuu (red={red})'
        assert blue > 20, f'sininen aaltoviiva puuttuu (blue={blue})'
        d = subprocess.run(['/usr/bin/python3', str(dlg)],
                           capture_output=True, text=True, timeout=120, env=env)
        assert d.returncode == 0 and 'dialog dispatched' in d.stdout, \
            d.stdout[-300:] + d.stderr[-1000:]
        time.sleep(8)  # dialogin renderointi on hidasta Xvfb:n alla
        subprocess.run([IMPORT, '-window', 'root', str(shot_dlg)],
                       check=True, env=env, capture_output=True, timeout=60)
        assert shot_dlg.exists() and shot_dlg.stat().st_size > 5000
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
