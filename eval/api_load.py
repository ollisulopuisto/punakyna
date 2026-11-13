"""API:n kuormitus- ja vivetesti: peräkkäiset ja rinnakkaiset pyynnöt.

Huom: sandbox-Linuxin luvut eivät ole Mac-viitteenä. Ajetaan paikallista
palvelinta vastaan erillisessä säikeessä.
"""
import json
import sys
import threading
import time

sys.path.insert(0, '.')
from punakyna.api import make_server

TEXT = ('Tämä on tavallinen suomenkielinen lause, jossa ei ole virheitä. '
        'Toinen lause seuraa ensimmäistä. Kolmas lause päättää kappaleen. ') * 8  # ~1,5 KB

def run(n_requests, n_threads, srv):
    url_port = srv.server_address[1]
    latencies = []
    lock = threading.Lock()

    def worker(count):
        import urllib.request
        body = json.dumps({'text': TEXT}).encode()
        for _ in range(count):
            req = urllib.request.Request(
                f'http://127.0.0.1:{url_port}/check', data=body,
                headers={'Content-Type': 'application/json'})
            t0 = time.perf_counter()
            with urllib.request.urlopen(req) as resp:
                resp.read()
            with lock:
                latencies.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    if n_threads == 1:
        worker(n_requests)
    else:
        threads = [threading.Thread(target=worker, args=(n_requests // n_threads,))
                   for _ in range(n_threads)]
        for t in threads: t.start()
        for t in threads: t.join()
    total = time.perf_counter() - t0
    lat = sorted(latencies)
    p50 = lat[len(lat)//2]; p95 = lat[int(len(lat)*0.95)]
    print(f'{n_threads:2d} säiettä x {n_requests//n_threads:3d} pyyntöä: '
          f'p50 {p50:6.1f} ms, p95 {p95:6.1f} ms, '
          f'kokonais {total:.1f} s ({len(lat)/total:.1f} req/s)')
    return latencies

if __name__ == '__main__':
    srv = make_server(port=0)  # ei tunnusta: vain suorituskykymittaus
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        run(10, 1, srv)      # lämmittely
        run(40, 1, srv)
        run(80, 8, srv)
        run(80, 16, srv)
    finally:
        srv.shutdown(); srv.server_close()
