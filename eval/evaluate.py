"""Savutestiarviointi: kasin rakennettu pieni aineisto.

Nama eivat ole erillinen (held-out) yleistyvan suorituskyvyn nayte:
ne toimivat regressiotestina ja kehitysajan tarkistuslistana. Raportoi
tulokset aina taman huomion kanssa. Oikea arviointi: FinnGEC-testiaineisto
(lisenssi/rajoitteet selvitettava, ks. README) tai vastaava lisensoitu data.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from punakyna.pipeline import check_text  # noqa


def load(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    here = os.path.dirname(__file__)
    errors = load(os.path.join(here, 'smoke_errors.jsonl'))
    clean = load(os.path.join(here, 'smoke_clean.jsonl'))

    for mode, kw in [('voikko-only (oikeinkirjoitus)',
                      dict(use_rules=False, use_gc=False)),
                     ('voikko-kokonaisuus (oikeinkirjoitus + voikko-gc)',
                      dict(use_rules=False, use_gc=True)),
                     ('punakyna (oikeinkirjoitus + saannot + voikko-gc)',
                      dict(use_rules=True, use_gc=True))]:
        det = Counter()
        det_ok = Counter()
        clean_fp = Counter()
        for item in errors:
            suggs = check_text(item['text'], **kw)
            rules = {s.rule for s in suggs}
            for want in item['expect']:
                base = want
                det[base] += 1
                if base in rules or (base == 'SPELL' and 'SPELL_UNKNOWN' in rules) \
                        or (base == 'DOUBLE_WORD' and 'VOIKKO_GC' in rules):
                    det_ok[base] += 1
        known_fp = Counter()
        for item in clean:
            allow = set(item.get('allow_rules', []))
            suggs = check_text(item['text'], **kw)
            for s in suggs:
                if s.severity in ('error', 'style'):
                    if s.rule in allow:
                        known_fp[s.rule] += 1
                    else:
                        clean_fp[s.rule] += 1
        print(f'\n=== {mode} ===')
        for rule in sorted(det):
            print(f'  havainto (virhejoukko): {rule}: {det_ok[rule]}/{det[rule]}')
        print(f'  vaarat halytykset puhtaassa joukossa: {sum(clean_fp.values())} '
              f'/ {len(clean)} lausetta, saannoittain: {dict(clean_fp)}')
        if known_fp:
            print(f'  tunnetut raja-tapaukset (allow_rules, ei lasketa vahingoksi): '
                  f'{dict(known_fp)}')


if __name__ == '__main__':
    main()
