"""API:n kovennustestit: tunnus, Host, Origin, CORS, content-type, rajat."""
import http.client
import json
import threading
import urllib.request
import urllib.error

import pytest

from punakyna.api import make_server, load_or_create_token, _valid_host_header

TOKEN = 'testitunnus-abc123'


@pytest.fixture
def server():
    srv = make_server(port=0, token=TOKEN)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _req(srv, path, method='POST', body=None, headers=None):
    conn = http.client.HTTPConnection('127.0.0.1', srv.server_address[1], timeout=10)
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, json.loads(data) if data else {}


def _good_body():
    return json.dumps({'text': 'Tämä on on testi.'}).encode()


def _good_headers():
    return {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}',
            'Host': '127.0.0.1'}


def test_ok_with_token_and_json(server):
    status, body = _req(server, '/check', body=_good_body(), headers=_good_headers())
    assert status == 200
    assert any(s['rule'] == 'DOUBLE_WORD' for s in body['suggestions'])


def test_missing_token_401(server):
    h = _good_headers(); del h['Authorization']
    status, _ = _req(server, '/check', body=_good_body(), headers=h)
    assert status == 401


def test_wrong_token_401(server):
    h = _good_headers(); h['Authorization'] = 'Bearer vaara'
    status, _ = _req(server, '/check', body=_good_body(), headers=h)
    assert status == 401


def test_dns_rebinding_bad_host_403(server):
    h = _good_headers(); h['Host'] = 'evil.example.com'
    status, _ = _req(server, '/check', body=_good_body(), headers=h)
    assert status == 403


def test_health_also_checks_host(server):
    status, _ = _req(server, '/health', method='GET', headers={'Host': 'evil.example.com'})
    assert status == 403


def test_unknown_origin_403(server):
    h = _good_headers(); h['Origin'] = 'https://evil.example.com'
    status, _ = _req(server, '/check', body=_good_body(), headers=h)
    assert status == 403


def test_allowlisted_origin_ok(server):
    srv = make_server(port=0, token=TOKEN, allowed_origins=('moz-extension://abc',))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        h = _good_headers(); h['Origin'] = 'moz-extension://abc'
        # portin vaihto: rakennetaan uusi yhteys srv:n porttiin
        conn = http.client.HTTPConnection('127.0.0.1', srv.server_address[1], timeout=10)
        conn.request('POST', '/check', body=_good_body(), headers=h)
        assert conn.getresponse().status == 200
        conn.close()
    finally:
        srv.shutdown(); srv.server_close()


def test_no_cors_headers(server):
    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    conn.request('POST', '/check', body=_good_body(), headers=_good_headers())
    resp = conn.getresponse(); resp.read()
    assert resp.getheader('Access-Control-Allow-Origin') is None
    conn.close()


def test_security_headers_present(server):
    """Palvelimen vastausten on sisällettävä turvaotsakkeet MIME-nuuskinnan ja kehyksiin upotuksen torjumiseksi."""
    # POST /check onnistunut vastaus
    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    conn.request('POST', '/check', body=_good_body(), headers=_good_headers())
    resp = conn.getresponse(); resp.read()
    assert resp.getheader('X-Content-Type-Options') == 'nosniff'
    assert resp.getheader('X-Frame-Options') == 'DENY'
    conn.close()

    # GET /health
    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    conn.request('GET', '/health', headers={'Host': '127.0.0.1'})
    resp = conn.getresponse(); resp.read()
    assert resp.getheader('X-Content-Type-Options') == 'nosniff'
    assert resp.getheader('X-Frame-Options') == 'DENY'
    conn.close()

    # Virhevastaukset (esim. 401, 404)
    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    conn.request('POST', '/check', body=_good_body(), headers={'Host': '127.0.0.1', 'Content-Type': 'application/json'})
    resp = conn.getresponse(); resp.read()
    assert resp.status == 401
    assert resp.getheader('X-Content-Type-Options') == 'nosniff'
    assert resp.getheader('X-Frame-Options') == 'DENY'
    conn.close()

    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    conn.request('GET', '/tuntematon', headers={'Host': '127.0.0.1'})
    resp = conn.getresponse(); resp.read()
    assert resp.status == 404
    assert resp.getheader('X-Content-Type-Options') == 'nosniff'
    assert resp.getheader('X-Frame-Options') == 'DENY'
    conn.close()


def test_unsupported_methods_handled_securely(server):
    """Käsittelemättömät metodit (501) palauttavat JSON:ia turvaotsakkeilla ilman Python-version vuotoa."""
    for method in ('TRACE', 'CONNECT', 'HEAD', 'CUSTOM'):
        conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
        conn.request(method, '/check')
        resp = conn.getresponse()
        assert resp.status == 501
        assert resp.getheader('X-Content-Type-Options') == 'nosniff'
        assert resp.getheader('X-Frame-Options') == 'DENY'
        assert resp.getheader('Content-Type') == 'application/json; charset=utf-8'
        server_header = resp.getheader('Server') or ''
        assert 'Python' not in server_header
        assert server_header == 'Punakyna/0.5'
        data = resp.read()
        if method != 'HEAD':
            body = json.loads(data)
            assert 'error' in body
        conn.close()


def test_options_preflight_rejected(server):
    status, _ = _req(server, '/check', method='OPTIONS',
                     headers={'Host': '127.0.0.1',
                              'Origin': 'https://evil.example.com',
                              'Access-Control-Request-Method': 'POST'})
    assert status == 404


def test_simple_request_form_rejected(server):
    h = _good_headers(); h['Content-Type'] = 'application/x-www-form-urlencoded'
    status, _ = _req(server, '/check', body=b'text=foo', headers=h)
    assert status == 415


def test_simple_request_textplain_rejected(server):
    h = _good_headers(); h['Content-Type'] = 'text/plain'
    status, _ = _req(server, '/check', body=b'{"text": "foo"}', headers=h)
    assert status == 415


def test_missing_content_length_411(server):
    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    # lähetetään runko chunked-koodauksella ilman Content-Length -arvoa
    conn.putrequest('POST', '/check')
    for k, v in _good_headers().items():
        conn.putheader(k, v)
    conn.putheader('Transfer-Encoding', 'chunked')
    conn.endheaders()
    conn.send(b'a\r\n{"text":"x"}\r\n0\r\n\r\n')
    resp = conn.getresponse(); resp.read()
    assert resp.status == 411
    conn.close()


def test_too_long_text_413(server):
    payload = json.dumps({'text': 'a' * 200_001}).encode()
    status, _ = _req(server, '/check', body=payload, headers=_good_headers())
    assert status == 413


def test_oversized_body_413_declared(server):
    h = _good_headers()
    conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
    conn.putrequest('POST', '/check')
    for k, v in h.items():
        conn.putheader(k, v)
    conn.putheader('Content-Length', str(2 * 1024 * 1024))
    conn.endheaders()
    resp = conn.getresponse(); resp.read()
    assert resp.status == 413
    conn.close()


def test_health_ok_no_token_needed(server):
    status, body = _req(server, '/health', method='GET', headers={'Host': 'localhost'})
    assert status == 200 and body['status'] == 'ok'


def test_non_loopback_bind_refused():
    with pytest.raises(ValueError):
        make_server(port=0, host='0.0.0.0')


def test_host_header_validator():
    # Hyväksytyt loopback-osoitteet portilla ja ilman
    assert _valid_host_header('127.0.0.1')
    assert _valid_host_header('127.0.0.1:8377')
    assert _valid_host_header('127.0.0.1:65535')
    assert _valid_host_header('localhost')
    assert _valid_host_header('localhost:8377')
    assert _valid_host_header('LOCALHOST:80')
    assert _valid_host_header('[::1]')
    assert _valid_host_header('[::1]:8377')
    assert _valid_host_header('::1')

    # Hylätyt osoitteet: ei-loopback, rebind-yritykset, virheelliset portit, ohjausmerkit
    assert not _valid_host_header('127.0.0.1.evil.com')
    assert not _valid_host_header('evil.com:127.0.0.1')
    assert not _valid_host_header('127.0.0.1:evil')
    assert not _valid_host_header('127.0.0.1:0')
    assert not _valid_host_header('127.0.0.1:65536')
    assert not _valid_host_header('127.0.0.1:99999')
    assert not _valid_host_header('[::1]:evil')
    assert not _valid_host_header('[::1]:65536')
    assert not _valid_host_header('foo@127.0.0.1')
    assert not _valid_host_header('127.0.0.1/foo')
    assert not _valid_host_header('')
    assert not _valid_host_header('   ')
    assert not _valid_host_header(None)
    assert not _valid_host_header(127001)


def test_token_file_created_0600(tmp_path):
    p = tmp_path / 'cfg' / 'token'
    token = load_or_create_token(p)
    assert token and load_or_create_token(p) == token
    assert (p.stat().st_mode & 0o777) == 0o600


# --- Kierros 2: tunnustiedoston kovennus ja rajat ---

import os
from punakyna.api import load_or_create_token as _lct, TokenError, make_server as _ms


def test_token_symlink_rejected(tmp_path):
    real = tmp_path / 'real'; real.write_text('x' * 40)
    link = tmp_path / 'token'; link.symlink_to(real)
    with pytest.raises(TokenError):
        _lct(link)


def test_token_loose_perms_rejected(tmp_path):
    p = tmp_path / 'token'; p.write_text('x' * 40); p.chmod(0o644)
    with pytest.raises(TokenError):
        _lct(p)


def test_token_short_rejected(tmp_path):
    p = tmp_path / 'token'; p.write_text('lyhyt'); p.chmod(0o600)
    with pytest.raises(TokenError):
        _lct(p)


def test_token_atomic_create_race(tmp_path):
    # toinen prosessi ehtii luoda: O_EXCL-heittoa ei saa tulla,
    # vaan luotu tunnus luetaan (FileExistsError käsitellään)
    p = tmp_path / 'token'
    t1 = _lct(p)
    assert _lct(p) == t1


def test_concurrency_bounded_still_serves():
    srv = _ms(port=0, token=TOKEN, max_workers=1)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        results = []
        def one():
            conn = http.client.HTTPConnection('127.0.0.1', srv.server_address[1], timeout=15)
            conn.request('POST', '/check', body=_good_body(), headers=_good_headers())
            results.append(conn.getresponse().status)
            conn.close()
        ts = [threading.Thread(target=one) for _ in range(4)]
        for t in ts: t.start()
        for t in ts: t.join()
        assert results == [200] * 4
    finally:
        srv.shutdown(); srv.server_close()


# --- Kierros 3: yhteysraja ja asiakkaan kovennus ---

def test_connection_cap_returns_503():
    srv = _ms(port=0, token=TOKEN, max_connections=2)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        port = srv.server_address[1]
        # pidä 2 yhteyttä auki hitaalla rungolla
        held = []
        for _ in range(2):
            c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
            c.putrequest('POST', '/check')
            for k, v in _good_headers().items():
                c.putheader(k, v)
            c.putheader('Content-Length', '100')
            c.endheaders()  # ei runkoa viela: yhteys jää auki
            held.append(c)
        import time; time.sleep(0.2)
        c3 = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        c3.request('GET', '/health', headers={'Host': '127.0.0.1'})
        resp = c3.getresponse(); resp.read()
        assert resp.status == 503
        c3.close()
        for c in held:
            c.close()
    finally:
        srv.shutdown(); srv.server_close()


def test_client_ignores_env_proxy(monkeypatch):
    from punakyna import client
    monkeypatch.setenv('http_proxy', 'http://evil-proxy:9999')
    monkeypatch.setenv('HTTP_PROXY', 'http://evil-proxy:9999')
    # jos proxya kaytettaisiin, yhteys epäonnistuisi; suora loopback toimii
    srv = _ms(port=0, token=TOKEN)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        suggs = client.check('Tämä on on testi.', port=srv.server_address[1], token=TOKEN)
        assert any(s['rule'] == 'DOUBLE_WORD' for s in suggs)
    finally:
        srv.shutdown(); srv.server_close()


def test_client_read_token_validates(tmp_path):
    from punakyna import client
    from punakyna.api import TokenError
    p = tmp_path / 'token'; p.write_text('x' * 40); p.chmod(0o644)
    with pytest.raises(TokenError):
        client.read_token(p)


def test_cap_is_pre_spawn_no_thread_growth():
    """Yli rajan yhteydet eivät saa synnyttää palvelinsäikeitä."""
    srv = _ms(port=0, token=TOKEN, max_connections=3)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        port = srv.server_address[1]
        base = threading.active_count()
        held = []
        for _ in range(3):
            c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
            c.putrequest('POST', '/check')
            for k, v in _good_headers().items():
                c.putheader(k, v)
            c.putheader('Content-Length', '100')
            c.endheaders()
            held.append(c)
        import time; time.sleep(0.3)
        during_held = threading.active_count()
        # 10 ylimääräistä yhteyttä: kaikki 503, ei uusia pysyviä säikeitä
        for _ in range(10):
            c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
            c.request('GET', '/health', headers={'Host': '127.0.0.1'})
            assert c.getresponse().status == 503
            c.close()
        time.sleep(0.3)
        assert threading.active_count() <= during_held
        assert during_held <= base + 3 + 1  # vain rajan verran työsäikeitä
        for c in held:
            c.close()
    finally:
        srv.shutdown(); srv.server_close()


# --- Sovelluskohtaiset tunnukset (per-app enrollment) ---

def test_token_map_multiple_apps():
    from punakyna.api import make_server as ms
    srv = ms(port=0, token_map={'libreoffice': 'tunnus-a-00000000000000000000000000000001',
                                'cli': 'tunnus-b-00000000000000000000000000000002'})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        for tok in ('tunnus-a-00000000000000000000000000000001',
                    'tunnus-b-00000000000000000000000000000002'):
            h = _good_headers(); h['Authorization'] = f'Bearer {tok}'
            status, _ = _req(srv, '/check', body=_good_body(), headers=h)
            assert status == 200
        h = _good_headers(); h['Authorization'] = 'Bearer tuntematon-00000000000000000000000000003'
        status, _ = _req(srv, '/check', body=_good_body(), headers=h)
        assert status == 401
    finally:
        srv.shutdown(); srv.server_close()


def test_app_token_lifecycle(tmp_path):
    from punakyna.tokenfile import (load_or_create_app_token, load_all_tokens,
                                    revoke_app_token, TokenError)
    d = tmp_path / 'tokens'
    t1 = load_or_create_app_token('libreoffice', d)
    t2 = load_or_create_app_token('cli', d)
    assert t1 != t2 and load_or_create_app_token('libreoffice', d) == t1
    all_t = load_all_tokens(d, fallback_path=tmp_path / 'token')
    assert all_t == {'cli': t2, 'libreoffice': t1}
    assert revoke_app_token('cli', d)
    assert not revoke_app_token('cli', d)
    assert load_all_tokens(d, fallback_path=tmp_path / 'token') == {'libreoffice': t1}
    with pytest.raises(TokenError):
        load_or_create_app_token('../pahis', d)
    with pytest.raises(TokenError):
        revoke_app_token('../pahis', d)
    with pytest.raises(TokenError):
        revoke_app_token('..\\pahis', d)


def test_revoke_app_token_path_traversal_prevented(tmp_path):
    from punakyna.tokenfile import revoke_app_token, TokenError
    tokens_dir = tmp_path / 'tokens'
    tokens_dir.mkdir()
    victim = tmp_path / 'victim.txt'
    victim.write_text('sensitive data')

    with pytest.raises(TokenError):
        revoke_app_token('../victim.txt', tokens_dir=tokens_dir)
    assert victim.exists()


def test_app_name_strict_allowlist_validation(tmp_path):
    """Sovellustunnisteen sallijalistatarkistus: hylkää ohjausmerkit,
    välimerkit, rivinvaihdot, piilotiedostot ja ylipituuden."""
    from punakyna.tokenfile import (load_or_create_app_token, read_app_token,
                                    revoke_app_token, TokenError)
    tokens_dir = tmp_path / 'tokens'
    # Hyväksytyt
    for valid_name in ('app', 'libreoffice', 'firefox-e2e', 'my_app.1'):
        tok = load_or_create_app_token(valid_name, tokens_dir=tokens_dir)
        assert read_app_token(valid_name, tokens_dir=tokens_dir) == tok

    # Kielletyt: CRLF, whitespace, ohjausmerkit, polkuerottimet, erikoismerkit
    invalid_names = [
        'app\nname', 'app\r\nname', 'app\tname', 'app name',
        'app/sub', 'app\\sub', 'app\0null',
        '.hidden', 'trailing.', '.', '..', '',
        'a' * 65, None, 123
    ]
    for invalid in invalid_names:
        with pytest.raises(TokenError):
            load_or_create_app_token(invalid, tokens_dir=tokens_dir)
        with pytest.raises(TokenError):
            read_app_token(invalid, tokens_dir=tokens_dir)
        with pytest.raises(TokenError):
            revoke_app_token(invalid, tokens_dir=tokens_dir)


def test_revoke_takes_effect_without_restart(tmp_path):
    """Peruutus voimaan AJONEUVON ollessa käynnissä: 200 -> poisto -> 401."""
    from punakyna.api import make_server as ms
    from punakyna.tokenfile import load_all_tokens, load_or_create_app_token, revoke_app_token
    d = tmp_path / 'tokens'
    tok = load_or_create_app_token('sovitin', d)
    srv = ms(port=0, tokens_provider=lambda: load_all_tokens(
        d, fallback_path=tmp_path / 'token'))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        h = _good_headers(); h['Authorization'] = f'Bearer {tok}'
        status, _ = _req(srv, '/check', body=_good_body(), headers=h)
        assert status == 200
        assert revoke_app_token('sovitin', d)
        status, _ = _req(srv, '/check', body=_good_body(), headers=h)
        assert status == 401  # heti, ei uudelleenkäynnistystä
    finally:
        srv.shutdown(); srv.server_close()


def _raw(srv, data, read_timeout=5):
    import socket
    sock = socket.create_connection(('127.0.0.1', srv.server_address[1]), timeout=read_timeout)
    sock.sendall(data)
    chunks = []
    try:
        while True:
            c = sock.recv(65536)
            if not c:
                break
            chunks.append(c)
    except socket.timeout:
        chunks.append(b'<<TIMEOUT>>')
    sock.close()
    return b''.join(chunks)


def test_unsupported_method_with_body_closes_connection(server):
    # send_error ei lue runkoa: yhteys on suljettava, ettei "junk" muutu seuraavaksi pyynnöksi.
    out = _raw(server, b'CUSTOM /check HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 4\r\n\r\n'
                       b'junkGET /health HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n')
    head = out.split(b'\r\n\r\n', 1)[0].lower()
    assert b'501' in out.split(b'\r\n', 1)[0]
    assert b'connection: close' in head
    assert b'<<timeout>>' not in out  # palvelin sulki yhteyden itse
    assert out.count(b'HTTP/1.') == 1  # ei toista vastausta jäännösrungosta


def test_head_fallback_has_no_body(server):
    out = _raw(server, b'HEAD /check HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n')
    head, _, body = out.partition(b'\r\n\r\n')
    assert b'501' in head.split(b'\r\n', 1)[0]
    assert b'content-length' in head.lower()
    assert body == b''
