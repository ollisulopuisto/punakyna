"""Rajapintojen offset-konventio (LUKITTU): kaikki pinnat - HTTP-API, CLI
--json, native messaging -isäntä - raportoivat sijainnit Python-
koodipisteinä subjektoidussa tekstissä. Ei UTF-16, ei tavuja.
Testattu emojilla (BMP:n ulkopuoli) ja yhdistävällä merkillä."""
import json
import struct
import subprocess
import sys
import threading

import pytest

from punakyna.api import make_server, load_or_create_token

CASES = [
    'Tämä on on testi.',
    '😀 Tämä on on testi.',               # emoji = 1 koodipiste
    'älto on on juttu.',            # ä = a + yhdistävä diakriitti
]


def expected_spans(text):
    i = text.index('on on')
    return [(i + 3, i + 5)]  # DOUBLE_WORD osoittaa toistuvan sanan


@pytest.fixture
def server(tmp_path):
    token = load_or_create_token(tmp_path / 'token')
    srv = make_server(port=0, token=token)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, token
    srv.shutdown(); srv.server_close()


def _api_spans(server, text):
    srv, token = server
    import urllib.request
    body = json.dumps({'text': text}).encode()
    req = urllib.request.Request(
        f'http://127.0.0.1:{srv.server_address[1]}/check', data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as resp:
        suggs = json.loads(resp.read())['suggestions']
    return sorted((s['start'], s['end']) for s in suggs if s['rule'] == 'DOUBLE_WORD')


def _cli_spans(text):
    proc = subprocess.run(
        [sys.executable, '-m', 'punakyna', '--json', '--no-spelling'],
        input=text, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    items = data if isinstance(data, list) else data.get('suggestions', data)
    return sorted((s['start'], s['end']) for s in items if s['rule'] == 'DOUBLE_WORD')


@pytest.mark.parametrize('text', CASES)
def test_api_spans_are_codepoints(server, text):
    assert _api_spans(server, text) == expected_spans(text)


@pytest.mark.parametrize('text', CASES)
def test_cli_spans_match_api(server, text):
    assert _cli_spans(text) == _api_spans(server, text)


def test_native_host_spans_match(server, monkeypatch):
    srv, token = server
    import punakyna.client as c
    monkeypatch.setattr(c, 'read_token', lambda path=None: token)
    sys.path.insert(0, 'adapters/browser')
    import importlib
    import native_host
    importlib.reload(native_host)

    for text in CASES:
        payload = json.dumps({'text': text}).encode()
        frames = struct.pack('<I', len(payload)) + payload
        import io

        class Buf(io.RawIOBase):
            def __init__(self, data=b''):
                self.data = bytearray(data); self.pos = 0
            def read(self, n=-1):
                if n < 0:
                    n = len(self.data) - self.pos
                out = bytes(self.data[self.pos:self.pos + n]); self.pos += n
                return out
            def write(self, b):
                self.data.extend(b); return len(b)
            def flush(self):
                pass

        class FakeStream:
            def __init__(self, data=b''):
                self.buffer = Buf(data)
        fake_in, fake_out = FakeStream(frames), FakeStream()
        real_in, real_out = sys.stdin, sys.stdout
        sys.stdin, sys.stdout = fake_in, fake_out
        try:
            native_host.main(api_port=srv.server_address[1])
        finally:
            sys.stdin, sys.stdout = real_in, real_out
        buf = bytes(fake_out.buffer.data)
        (ln,) = struct.unpack('<I', buf[:4])
        resp = json.loads(buf[4:4 + ln])
        spans = sorted((s['start'], s['end']) for s in resp['suggestions']
                       if s['rule'] == 'DOUBLE_WORD')
        assert spans == expected_spans(text), f'{text!r}: {spans}'
