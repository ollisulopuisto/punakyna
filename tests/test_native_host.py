"""Native messaging -isännän protokollatesti: kehystys ja pyyntö/vastaus."""
import json
import struct
import sys
import threading

import pytest

from punakyna.api import make_server, load_or_create_token


@pytest.fixture
def stack(tmp_path):
    token = load_or_create_token(tmp_path / 'token')
    srv = make_server(port=0, token=token)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1], token
    srv.shutdown(); srv.server_close()


def _frame(obj):
    data = json.dumps(obj).encode()
    return struct.pack('<I', len(data)) + data


def _run_host(stack, frames, monkeypatch):
    api_port, token = stack
    import punakyna.client as c
    # ohjaa isännän tunnusluku fixture-tunnukseen
    monkeypatch.setattr(c, 'read_token', lambda path=None: token)
    import importlib
    sys.path.insert(0, 'adapters/browser')
    import native_host
    importlib.reload(native_host)

    class FakeStream:
        class _Buf:
            def __init__(self, data=b''):
                self.data = bytearray(data)
                self.pos = 0
            def read(self, n=-1):
                if n < 0:
                    n = len(self.data) - self.pos
                out = bytes(self.data[self.pos:self.pos+n])
                self.pos += n
                return out
            def write(self, b):
                self.data.extend(b)
            def flush(self):
                pass
        def __init__(self, data=b''):
            self.buffer = self._Buf(data)
    fake_in, fake_out = FakeStream(frames), FakeStream()
    real_in, real_out = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = fake_in, fake_out
    try:
        native_host.main(api_port=api_port)
    finally:
        sys.stdin, sys.stdout = real_in, real_out
    # pura vastauskehykset
    buf, out = bytes(fake_out.buffer.data), []
    pos = 0
    while pos + 4 <= len(buf):
        (ln,) = struct.unpack('<I', buf[pos:pos+4])
        out.append(json.loads(buf[pos+4:pos+4+ln]))
        pos += 4 + ln
    return out


def test_host_roundtrip(stack, monkeypatch):
    responses = _run_host(stack, _frame({'text': 'Tämä on on testi.'}), monkeypatch)
    assert any(s.get('rule') == 'DOUBLE_WORD'
               for s in responses[0]['suggestions'])


def test_host_bad_message_errors(stack, monkeypatch):
    responses = _run_host(stack, _frame({'ei': 'tekstia'}), monkeypatch)
    assert 'error' in responses[0]


def test_host_eof_exits(stack, monkeypatch):
    assert _run_host(stack, b'', monkeypatch) == []


def test_host_truncated_header_exits_cleanly(stack, monkeypatch):
    assert _run_host(stack, b'\x05\x00', monkeypatch) == []


def test_host_truncated_body_errors(stack, monkeypatch):
    import struct as st
    frame = st.pack('<I', 100) + b'{"text": "lyhyt"}'  # luvattu 100, tuli 17
    responses = _run_host(stack, frame, monkeypatch)
    assert responses and 'error' in responses[0]


def test_host_huge_length_prefix_errors(stack, monkeypatch):
    import struct as st
    responses = _run_host(stack, st.pack('<I', 3 * 1024 * 1024) + b'{}', monkeypatch)
    assert responses and 'error' in responses[0]


def test_host_garbage_json_errors(stack, monkeypatch):
    responses = _run_host(stack, _frame_raw(b'not json at all'), monkeypatch)
    assert responses and 'error' in responses[0]


def test_host_non_dict_errors(stack, monkeypatch):
    responses = _run_host(stack, _frame(['lista']), monkeypatch)
    assert responses and 'error' in responses[0]


def test_host_stdout_only_frames(stack, monkeypatch):
    """stdout saa sisaltaa vain purkautuvia kehyksia - ei logia/tracebackia."""
    frames = (_frame({'text': 'Tämä on on testi.'})
              + _frame_raw(b'rikki')
              + _frame({'text': 'siisti lause.'}))
    responses = _run_host(stack, frames, monkeypatch)
    assert len(responses) == 3  # jokaiseen tuli kehys, parseri ei takeltunut


def _frame_raw(data):
    import struct as st
    return st.pack('<I', len(data)) + data
