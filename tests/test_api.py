import json
import threading
import urllib.request
import urllib.error

import pytest

from punakyna.api import make_server


@pytest.fixture
def server():
    srv = make_server(port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _post(srv, path, payload, raw=None):
    data = raw if raw is not None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'http://127.0.0.1:{srv.server_address[1]}{path}', data=data,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_check_flags_double_word(server):
    status, body = _post(server, '/check', {'text': 'Tämä on on testi.'})
    assert status == 200
    rules = {s['rule'] for s in body['suggestions']}
    assert 'DOUBLE_WORD' in rules


def test_check_clean_text_empty(server):
    status, body = _post(server, '/check', {'text': 'Tämä lause on oikein.'})
    assert status == 200
    assert isinstance(body['suggestions'], list)


def test_health(server):
    with urllib.request.urlopen(
            f'http://127.0.0.1:{server.server_address[1]}/health') as resp:
        assert resp.status == 200
        assert json.loads(resp.read())['status'] == 'ok'


def test_get_check_method_not_allowed(server):
    req = urllib.request.Request(
        f'http://127.0.0.1:{server.server_address[1]}/check')
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 405


def test_unknown_path_404(server):
    status, _ = _post(server, '/tiedot', {'text': 'x'})
    assert status == 404


def test_bad_payload_400(server):
    status, _ = _post(server, '/check', {'ei_tekstia': True})
    assert status == 400


def test_oversized_413(server):
    # Python 3.12+: palvelin lahettaa 413:n ja sulkee yhteyden ennen kuin
    # megatavun runko ehtii siirtya; asiakas nakee BrokenPipen vastauksen
    # sijaan. Molemmat todistavat, etta ylisuuri runko hylattiin.
    data = b'x' * (1024 * 1024 + 1)
    req = urllib.request.Request(
        f'http://127.0.0.1:{server.server_address[1]}/check', data=data,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 413
    except urllib.error.HTTPError as e:
        assert e.code == 413
    except urllib.error.URLError as e:
        assert isinstance(e.reason, (BrokenPipeError, ConnectionResetError)), e
    # Palvelin jatkoi normaalisti hajonnutta lahetysta jalkeen.
    status, _ = _post(server, '/check', {'text': 'Tämä lause on oikein.'})
    assert status == 200


def test_refuses_non_loopback():
    with pytest.raises(ValueError):
        make_server(port=0, host='0.0.0.0')


def test_optional_style_profile(server):
    text = 'Hakemus lähetetään huomenna.'
    status, body = _post(server, '/check', {'text': text})
    assert status == 200
    assert not any(s['rule'].startswith('STYLE_') for s in body['suggestions'])
    status, body = _post(server, '/check', {'text': text, 'style_profile': {'prefer_active': True}})
    assert status == 200
    assert any(s['rule'] == 'STYLE_ACTOR' for s in body['suggestions'])
    assert _post(server, '/check', {'text': text, 'style_profile': {'reader': 'invalid'}})[0] == 400
