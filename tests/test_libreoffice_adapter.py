"""Sovitintesti TODELLA LibreOfficella (Linux, headless UNO).
EI Mac-validointi eikä asennettu laajennos. Skippaa jos soffice/uno puuttuu.
UNO-ajot tehdaan jarjestelman /usr/bin/python3:lla (venv:ssa ei uno-moduulia)."""
import shutil
import subprocess
import threading

import pytest

from punakyna.api import make_server, load_or_create_token

SYS_PY = '/usr/bin/python3'


def _uno_ok():
    if shutil.which('soffice') is None:
        return False
    r = subprocess.run([SYS_PY, '-c', 'import uno'], capture_output=True)
    return r.returncode == 0


pytestmark = pytest.mark.skipif(not _uno_ok(), reason='soffice tai uno puuttuu')

DOC_TEXT = ('Tämä on ensimmäinen kappale ilman virheitä.\n'
            '😀 Emojin jälkeen on on tuplasana.\n'
            'Kolmannessa kappaleessa on rivinvaihto\x0bja on on tupla.')
# odotus: emoji-rivillä virheen UNO-alku = koodipisteindeksi+1


@pytest.fixture(scope='module')
def lo_stack(tmp_path_factory):
    tmp = tmp_path_factory.mktemp('lo')
    profile = tmp / 'loprofile'
    token_path = tmp / 'token'
    token = load_or_create_token(token_path)
    srv = make_server(port=0, token=token)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    api_port = srv.server_address[1]

    proc = subprocess.Popen([
        'soffice', '--headless', '--norestore', '--nologo',
        f'-env:UserInstallation=file://{profile}',
        '--accept=socket,host=127.0.0.1,port=2002;urp;'])

    r = subprocess.run([SYS_PY, 'adapters/libreoffice/_make_doc.py', DOC_TEXT],
                       capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, f'asiakirjan luonti epäonnistui: {r.stderr}'

    yield api_port, token_path

    subprocess.run([SYS_PY, '-c',
                    'import uno; c=uno.getComponentContext();'
                    'r=c.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver",c);'
                    'x=r.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext");'
                    'd=x.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop",x);'
                    'd.terminate()'],
                   capture_output=True, timeout=30)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
    srv.shutdown(); srv.server_close()


def test_adapter_finds_double_word_in_real_libreoffice(lo_stack):
    api_port, token_path = lo_stack
    import os
    env = dict(os.environ, PYTHONPATH='.')
    out = subprocess.run(
        [SYS_PY, 'adapters/libreoffice/punakyna_lo.py',
         '--port', '2002', '--api-port', str(api_port),
         '--token-path', str(token_path)],
        capture_output=True, text=True, timeout=60, env=env)
    assert out.returncode == 0, out.stderr
    lines = [l for l in out.stdout.splitlines() if 'DOUBLE_WORD' in l]
    assert len(lines) == 2, out.stdout
    # DOUBLE_WORD osoittaa TOISTUVAN sanan: emoji-kappaleessa toisen 'on'-san
    # koodipisteindeksi on 20, UNO-positio 21 (emoji = 2 UTF-16-yksikköä)
    assert lines[0].startswith('kappale 1, merkit 20-22 (UTF-16: 21-23)'), lines
    assert lines[1].startswith('kappale 2, merkit '), lines
    assert 'Yhteensä 2' in out.stdout


def _read_props(para, start, end):
    r = subprocess.run([SYS_PY, 'adapters/libreoffice/_read_props.py',
                        str(para), str(start), str(end)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_adapter_highlights_in_real_document(lo_stack):
    import os
    api_port, token_path = lo_stack
    env = dict(os.environ, PYTHONPATH='.')
    out = subprocess.run(
        [SYS_PY, 'adapters/libreoffice/punakyna_lo.py',
         '--port', '2002', '--api-port', str(api_port),
         '--token-path', str(token_path), '--highlight'],
        capture_output=True, text=True, timeout=60, env=env)
    assert out.returncode == 0, out.stderr
    # kappale 1: emoji + toistuva 'on' koodipisteissä 20-22
    # (goRight laskee koodipisteitä - todettu emoji-testillä)
    props = _read_props(1, 20, 22)
    assert 'underline=0' not in props, props
    assert "text='on'" in props, props  # korostus osui juuri toistuvaan sanaan
    assert 'color=16711680' in props    # punainen
    # siisti kappale 0 ei saa olla korostettu
    props0 = _read_props(0, 0, 4)
    assert 'underline=0' in props0, props0
    # --clear palauttaa
    out2 = subprocess.run(
        [SYS_PY, 'adapters/libreoffice/punakyna_lo.py',
         '--port', '2002', '--api-port', str(api_port),
         '--token-path', str(token_path), '--clear'],
        capture_output=True, text=True, timeout=60, env=env)
    assert out2.returncode == 0, out2.stderr
    assert 'underline=0' in _read_props(1, 20, 22)


def _run_adapter(lo_stack, *extra):
    import os
    api_port, token_path = lo_stack
    env = dict(os.environ, PYTHONPATH='.')
    return subprocess.run(
        [SYS_PY, 'adapters/libreoffice/punakyna_lo.py',
         '--port', '2002', '--api-port', str(api_port),
         '--token-path', str(token_path), *extra],
        capture_output=True, text=True, timeout=60, env=env)


def test_clear_restores_user_original_formatting(lo_stack):
    """Käyttäjän OMA alleviivaus+väri säilyy: clear palauttaa ne tasan."""
    r = subprocess.run([SYS_PY, 'adapters/libreoffice/_preformat.py', '1', '20', '22'],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    out = _run_adapter(lo_stack, '--highlight')
    assert out.returncode == 0, out.stderr
    assert 'HUOM: korostus muuttaa' in out.stderr
    props = _read_props(1, 20, 22)
    assert 'underline=10' in props and 'color=16711680' in props  # meidän korostus
    out2 = _run_adapter(lo_stack, '--clear')
    assert out2.returncode == 0, out2.stderr
    props = _read_props(1, 20, 22)
    assert 'underline=1' in props and 'color=255' in props, props  # käyttäjän oma takaisin
    # siivoa käyttäjän muotoilu pois jatkotestejä varten
    r = subprocess.run([SYS_PY, '-c', '''
import uno, time
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
enum = doc.Text.createEnumeration()
i = 0
while enum.hasMoreElements():
    p = enum.nextElement()
    if p.supportsService("com.sun.star.text.Paragraph"):
        if i == 1:
            c = doc.Text.createTextCursorByRange(p.Start)
            c.goRight(20, False); c.goRight(2, True)
            c.CharUnderline = 0; c.CharUnderlineHasColor = False
            break
        i += 1
print("cleansed")'''], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr


def test_repeated_highlight_runs_then_clear_restores(lo_stack):
    """Toistuvat highlight-ajot eivät kapseloi omaa korostusta 'alkuperäiseksi'."""
    before = _read_props(1, 20, 22)
    for _ in range(2):
        out = _run_adapter(lo_stack, '--highlight')
        assert out.returncode == 0, out.stderr
        assert 'underline=10' in _read_props(1, 20, 22)
    out = _run_adapter(lo_stack, '--clear')
    assert out.returncode == 0, out.stderr
    assert _read_props(1, 20, 22) == before


def test_edit_between_highlight_and_clear_warns_and_skips(lo_stack):
    out = _run_adapter(lo_stack, '--highlight')
    assert out.returncode == 0, out.stderr
    r = subprocess.run([SYS_PY, 'adapters/libreoffice/_edit_doc.py', '1'],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    out2 = _run_adapter(lo_stack, '--clear')
    assert out2.returncode == 0, out2.stderr
    assert 'varoitus' in out2.stderr, out2.stderr
    assert 'ohitettu' in out2.stdout
