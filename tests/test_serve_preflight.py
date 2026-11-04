# -*- coding: utf-8 -*-
"""Palvelimen käynnistyksen esitarkistus ja siisti moottorivirhe.

preflight_engine(): libvoikko-latausvika -> SystemExit toimenpideohjeella
(ei tracebackia vasta ensimmäisestä pyynnöstä). do_POST: moottorin
odottamaton virhe -> 500 JSON, ei yhteyden katkaisua tracebackin kera.
"""
import json
import threading
import urllib.error
import urllib.request

import pytest

from punakyna import api
from punakyna.tokenfile import load_or_create_token


def test_preflight_failure_is_actionable(monkeypatch):
    def boom():
        raise OSError("dlopen(libvoikko.1.dylib, 0x0006): tried: ...")
    monkeypatch.setattr('punakyna.backend_voikko.get_voikko', boom)
    with pytest.raises(SystemExit) as exc:
        api.preflight_engine()
    msg = str(exc.value)
    assert 'libvoikko' in msg
    assert 'brew install libvoikko voikko-fi' in msg
    assert 'PUNAKYNA_LIBVOIKKO_PATH' in msg


def test_preflight_success_is_silent(monkeypatch):
    monkeypatch.setattr('punakyna.backend_voikko.get_voikko', lambda: object())
    assert api.preflight_engine() is None


@pytest.fixture
def server(tmp_path):
    token = load_or_create_token(tmp_path / 'token')
    srv = api.make_server(port=0, token=token)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, token
    srv.shutdown()
    srv.server_close()


def _post(port, token, payload):
    req = urllib.request.Request(
        f'http://127.0.0.1:{port}/check', data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + token})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_engine_error_is_clean_500_not_traceback(monkeypatch, server):
    srv, token = server

    def boom(*a, **kw):
        raise OSError('dlopen failed')
    monkeypatch.setattr('punakyna.api.check_text', boom)
    status, body = _post(srv.server_address[1], token, {'text': 'Me olen.'})
    assert status == 500
    assert 'error' in body
    assert 'OSError' in body['error']
    assert 'Traceback' not in body['error']


def test_runtime_error_stays_400(monkeypatch, server):
    srv, token = server

    def boom(*a, **kw):
        raise RuntimeError('stanza puuttuu')
    monkeypatch.setattr('punakyna.api.check_text', boom)
    status, body = _post(srv.server_address[1], token, {'text': 'Me olen.'})
    assert status == 400
    assert 'stanza' in body['error']
