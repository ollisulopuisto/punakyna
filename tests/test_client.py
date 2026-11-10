"""Päästä päähän -testi: asiakaskirjasto vs. oikea palvelin + tunnustiedosto."""
import threading

import pytest

from punakyna.api import make_server, load_or_create_token
from punakyna import client


@pytest.fixture
def running(tmp_path):
    token_path = tmp_path / 'token'
    token = load_or_create_token(token_path)
    srv = make_server(port=0, token=token)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, token, token_path
    srv.shutdown(); srv.server_close()


def test_end_to_end_check_via_client(running):
    srv, token, token_path = running
    suggs = client.check('Tämä on on testi.',
                         port=srv.server_address[1], token=client.read_token(token_path))
    assert any(s['rule'] == 'DOUBLE_WORD' for s in suggs)


def test_client_reads_token_file_by_default(running, tmp_path, monkeypatch):
    srv, token, token_path = running
    monkeypatch.setattr(client, 'TOKEN_PATH', token_path)
    # read_token käyttää oletuspolkua parametrina; annetaan se suoraan
    assert client.read_token(token_path) == token


def test_client_connection_error_suomeksi():
    with pytest.raises(ConnectionError) as e:
        client.check('hei', port=59998, token='x', timeout=2)
    assert 'käynnistettykö' in str(e.value)


def test_client_wrong_token_raises(running):
    srv, token, _ = running
    import urllib.error
    with pytest.raises(urllib.error.HTTPError) as e:
        client.check('hei', port=srv.server_address[1], token='vaara-tunnus-00000000000000000000')
    assert e.value.code == 401


def test_client_refuses_non_loopback_hosts():
    for bad_host in ('evil.com', '192.168.1.1', '10.0.0.1', '127.0.0.1.evil.com', 'example.org'):
        with pytest.raises(ValueError, match='vain loopback sallittu'):
            client.check('hei', host=bad_host, token='testi-tunnus-000000000000000000000')
