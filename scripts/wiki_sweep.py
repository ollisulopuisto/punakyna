"""Tarkkuusmittaus: aja putki fi.wikipedia-artikkeleihin ja raportoi osumat.

Käyttö: uv run python scripts/wiki_sweep.py [--rules TYPO_RANGE_HYPHEN,...] [--limit 40]
Artikkelit on kiinteä lista (toistettavuus); kattavuus ~lajiteltuja aiheita.
Mikään osuma ei ole automaattisesti virhe - raportoi kontekstit silmäilyä varten.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ARTICLES = [
    'Suomi', 'Helsinki', 'Jääkiekko', 'Formula 1', 'Boeing 737',
    'Suomen historia', 'Toinen maailmansota', 'Nokia', 'Linux', 'Matematiikka',
    'Fysiikka', 'Jean Sibelius', 'Jalkapallo', 'Euroopan unioni', 'Talvisota',
    'Kirjallisuus', 'Aleksis Kivi', 'Tietokone', 'Ohjelmointi', 'Viini',
    'Rautatie', 'Helsinki-Vantaan lentoasema', 'Puhelin', 'Internet',
]


def fetch_all(titles):
    out = {}
    for i in range(0, len(titles), 1):
        batch = titles[i:i + 1]
        url = ('https://fi.wikipedia.org/w/api.php?action=query&prop=extracts'
               '&explaintext=1&exlimit=max&format=json&redirects=1&titles='
               + urllib.parse.quote('|'.join(batch)))
        req = urllib.request.Request(url, headers={
            'User-Agent': 'punakyna-eval/0.1 (github.com/ollisulopuisto/punakyna)'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    time.sleep(10 * (attempt + 1))
                    continue
                raise
        for page in data['query']['pages'].values():
            out[page['title']] = page.get('extract', '')
        time.sleep(2)
    return out


def main():
    rules = None
    limit = len(ARTICLES)
    args = sys.argv[1:]
    if '--rules' in args:
        rules = set(args[args.index('--rules') + 1].split(','))
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    from punakyna.pipeline import check_text
    counts = {}
    samples = {}
    words = 0
    texts = fetch_all(ARTICLES[:limit])
    for title, text in texts.items():
        words += len(text.split())
        for s in check_text(text, use_spelling=False):
            if rules and s.rule not in rules:
                continue
            counts[s.rule] = counts.get(s.rule, 0) + 1
            samples.setdefault(s.rule, []).append(
                (title, text[max(0, s.start - 40):s.end + 40].replace('\n', ' ')))
    print('artikkeleita:', min(limit, len(ARTICLES)), 'sanoja:', words)
    for rule, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'{rule}: {n}')
        for title, ctx in samples[rule][:12]:
            print(f'  [{title}] ...{ctx}...')


if __name__ == '__main__':
    main()
