"""Regression: 8 rinnakkaista asiakasta kaatoi ennen palvelimen libvoikko-
heap-korruptioon. Ajetaan aliprosessissa, jotta kaatuminen olisi nakyva."""
import json
import subprocess
import sys
import textwrap

SCRIPT = textwrap.dedent('''
    import json, threading, urllib.request, sys
    from punakyna.api import make_server
    srv = make_server(port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    body = json.dumps({'text': 'Tämä on tavallinen suomenkielinen lause. ' * 20}).encode()
    results = []
    lock = threading.Lock()
    def worker():
        for _ in range(5):
            req = urllib.request.Request(
                f'http://127.0.0.1:{port}/check', data=body,
                headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:
                with lock:
                    results.append(resp.status)
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    print('RESULTS', results)
    sys.exit(0 if results == [200] * 40 else 1)
''')


def test_8_concurrent_clients_no_crash():
    proc = subprocess.run(
        [sys.executable, '-c', SCRIPT], capture_output=True, text=True,
        timeout=120, cwd='.')
    assert proc.returncode == 0, (
        f'palvelinprosessi kaatui tai virhe: rc={proc.returncode}\n'
        f'{proc.stdout}\n{proc.stderr}')
    assert 'RESULTS' in proc.stdout
