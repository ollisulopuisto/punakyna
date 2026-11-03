"""TODELLINEN selain-end-to-end: Firefox ESR + native messaging.

Ketju: Firefox lataa tilapäisen laajennuksen -> taustaskripti lähettää
tekstin native-isännälle -> isäntä kysyy paikalliselta API:ta
SOVELLUSKOHTAISELLA bearer-tunnuksella (firefox-e2e, enrollment ->
peruutus samassa testissä) -> laajennos raportoi vastauksen testin
tarkkailupalvelimelle HTTP:lla.

Laajuus (tärkeää): tämä on kehitystason automaatio, EI julkaisupakkaus.
Laajennos ladataan väliaikaisprofililla ja xpinstall.signatures.required=false
-asetuksella; julkaisu vaatii allekirjoitetun .xpi:n ja pysyvän manifestin
käyttäjän profiiliin - niitä ei tehdä eikä testata tässä.
google-chrome ohittaa --load-extension:in (brändätty Chrome), siksi Firefox.

Ympäristön koskemattomuus: testi kirjoittaa vain tmp_pathiin ja kahteen
tunnettuun tiedostoon, jotka poistetaan finally-lohkossa myös virheessä:
~/.mozilla/native-messaging-hosts/fi.punakyna.host.json (ja hakemisto, jos
testi loi sen) sekä ~/.config/punakyna/tokens/firefox-e2e.
"""
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from punakyna import client
from punakyna.api import make_server
from punakyna.tokenfile import (
    load_or_create_token, load_or_create_app_token, load_all_tokens,
    revoke_app_token, TOKENS_DIR)

FF = shutil.which('firefox-esr') or shutil.which('firefox')
pytestmark = pytest.mark.skipif(FF is None, reason='firefox puuttuu')

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT_ID = 'punakyna-e2e@test.invalid'
APP = 'firefox-e2e'
OBS_PORT = 8398
API_PORT = 8377


class Observer(BaseHTTPRequestHandler):
    hits = []

    def do_GET(self):
        Observer.hits.append(self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *a):
        pass


def test_firefox_native_messaging_end_to_end(tmp_path):
    load_or_create_token()
    api = make_server(port=API_PORT, tokens_provider=load_all_tokens)
    threading.Thread(target=api.serve_forever, daemon=True).start()
    obs = HTTPServer(('127.0.0.1', OBS_PORT), Observer)
    threading.Thread(target=obs.serve_forever, daemon=True).start()
    Observer.hits.clear()

    # Enrollment (sama toimi kuin CLI:n --enroll-app): erillinen tunnus.
    app_token = load_or_create_app_token(APP)
    legacy = client.read_token()
    assert app_token != legacy, 'sovellustunnus saa olla sama kuin perustunnus'

    wrapper = tmp_path / 'host.sh'
    wrapper.write_text(f"""#!/bin/sh
export PYTHONPATH={REPO}
export PUNAKYNA_APP={APP}
export PUNAKYNA_LIBVOIKKO_PATH={os.environ.get('PUNAKYNA_LIBVOIKKO_PATH', '')}
export PUNAKYNA_VOIKKO_DICTIONARY_PATH={os.environ.get('PUNAKYNA_VOIKKO_DICTIONARY_PATH', '')}
exec /usr/bin/python3 {REPO}/adapters/browser/native_host.py
""")
    wrapper.chmod(0o755)

    nm_dir = os.path.expanduser('~/.mozilla/native-messaging-hosts')
    made_nm_dir = not os.path.isdir(nm_dir)
    os.makedirs(nm_dir, exist_ok=True)
    host_manifest = os.path.join(nm_dir, 'fi.punakyna.host.json')
    with open(host_manifest, 'w') as f:
        json.dump({'name': 'fi.punakyna.host', 'description': 'Punakynä E2E',
                   'path': str(wrapper), 'type': 'stdio',
                   'allowed_extensions': [EXT_ID]}, f)

    extdir = tmp_path / 'ext'
    extdir.mkdir()
    (extdir / 'manifest.json').write_text(json.dumps({
        'manifest_version': 2,
        'name': 'Punakyna E2E',
        'version': '0.0.1',
        'permissions': ['nativeMessaging', f'http://127.0.0.1:{OBS_PORT}/'],
        'browser_specific_settings': {'gecko': {'id': EXT_ID}},
        'background': {'scripts': ['background.js'], 'persistent': True},
    }))
    (extdir / 'background.js').write_text(f"""
browser.runtime.sendNativeMessage('fi.punakyna.host',
  {{text: 'Tämä on on testi.'}}).then(resp => {{
    const rules = (resp.suggestions || []).map(s => s.rule).join(',');
    return fetch('http://127.0.0.1:{OBS_PORT}/report?rules=' + rules);
  }}).catch(e => fetch('http://127.0.0.1:{OBS_PORT}/report?error=' + e));
""")

    profile = tmp_path / 'ffprofile'
    (profile / 'extensions').mkdir(parents=True)
    (profile / 'user.js').write_text(
        'user_pref("xpinstall.signatures.required", false);\n'
        'user_pref("extensions.autoDisableScopes", 14);\n'
        'user_pref("extensions.enabledScopes", 15);\n'
        'user_pref("browser.shell.checkDefaultBrowser", false);\n'
        'user_pref("datareporting.policy.dataSubmissionEnabled", false);\n')
    xpi = profile / 'extensions' / f'{EXT_ID}.xpi'
    with zipfile.ZipFile(xpi, 'w') as z:
        z.write(extdir / 'manifest.json', 'manifest.json')
        z.write(extdir / 'background.js', 'background.js')

    try:
        proc = subprocess.Popen(
            [FF, '--headless', '--no-remote', '--profile', str(profile),
             'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 45
        try:
            while time.time() < deadline:
                if Observer.hits:
                    break
                time.sleep(0.5)
            assert Observer.hits, 'laajennos ei raportoinut 45 s kuluessa'
            hit = Observer.hits[0]
            assert 'error=' not in hit, hit
            assert 'DOUBLE_WORD' in hit, hit
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        # Peruutus palvelimen OLLESSA käynnissä -> 401 ilman uudelleenkäynnistystä.
        revoke_app_token(APP)
        with pytest.raises(urllib.error.HTTPError) as exc:
            client.check('Tämä on on testi.', port=API_PORT, token=app_token)
        assert exc.value.code == 401
        # Perustunnus toimii edelleen: peruutus oli sovelluskohtainen.
        assert client.check('Tämä on on testi.', port=API_PORT,
                            token=legacy)
    finally:
        api.shutdown(); api.server_close()
        obs.shutdown(); obs.server_close()
        # Ympäristön palautus myös virhepolulla:
        revoke_app_token(APP)
        if os.path.exists(host_manifest):
            os.unlink(host_manifest)
        if made_nm_dir and os.path.isdir(nm_dir):
            os.rmdir(nm_dir)
    # Loppuvahvistus: käyttäjän ympäristö ennallaan.
    assert not os.path.exists(host_manifest)
    assert not (TOKENS_DIR / APP).exists()
