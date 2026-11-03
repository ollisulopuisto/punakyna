"""Erillinen (held-out) arviointi DaLA Finnish -aineistolla.

Aineisto: schneiderkamplab/dala-fi-audited, config=correction, split=test
  https://huggingface.co/datasets/schneiderkamplab/dala-fi-audited
Lisenssi: source-specific (LICENSE.md); lahteena Finnish Wikipedia,
  tietuekohtainen lisenssi CC-BY-SA-3.0; GFDL, attribuutio sailytettava.
Rajoitteet (aineistokortin mukaan): synteettiset korruptiot, automaattinen
  (Gemma) auditointi, EI aidon puhujan validoima eika kultastandardi.
  Tasta syysta lukuja ei saa esittaa ihmisannotoidun testijoukon tuloksina.

Ei kontaminaatiota: punakynan saannot kirjoitettiin ennen taman aineiston
tarkastelua. Lahteiden kartoituksessa nahtiin HF-katselimessa ~25 rivia
acceptability-konfiguraation alkupaaasta; arviointi kayttaa correction-
konfiguraation test-jakoa, jonka riveja ei ole tarkasteltu ennen ajoa.

Mitat (laucetasolla):
- havainto: liputtaako punakyna korruptoituneen lauseen (mika tahansa
  error/style-ehdotus), corruption_type-kohtaisesti
- yli-korjaus: liputtaako punakyna puhtaan kontrollilauseen
Nama ovat karkeita laucetason mittareita: havainto ei takaa etta osuma
kohdistuu juuri korruptoituneeseen kohtaan, ja osa "puhtaista" lauseista
voi sisaltaa aitoja Wikipedia-virheita (aineistokortin mainitsemat).

Kaytto:
  python eval/heldout_dala.py /tmp/dala_fi_correction_test.jsonl.gz [n_parit]
"""
import gzip
import json
import random
import sys
from collections import Counter

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from punakyna.pipeline import check_text  # noqa


def sentence_of(row):
    content = row['messages'][0]['content']
    return content.split('\n\n', 1)[1].strip()


def main():
    path = sys.argv[1]
    n_pairs = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    pairs = {}
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            m = row['metadata']
            if m['split'] != 'test':
                continue
            p = pairs.setdefault(m['pair_id'], {})
            p[m['variant']] = (sentence_of(row), tuple(m['corruption_types']))
    keys = sorted(pairs)
    random.Random(42).shuffle(keys)
    keys = [k for k in keys if 'corrupted' in pairs[k] and 'clean' in pairs[k]][:n_pairs]
    print(f'pareja valittu: {len(keys)} (seed=42)')

    det = Counter()
    det_tot = Counter()
    clean_flags = Counter()
    clean_flagged = 0
    for i, k in enumerate(keys):
        corrupt_text, ctypes_ = pairs[k]['corrupted']
        clean_text, _ = pairs[k]['clean']
        suggs = check_text(corrupt_text)
        flagged = {s.rule for s in suggs if s.severity in ('error', 'style')}
        for t in ctypes_ or ('(none)',):
            det_tot[t] += 1
            if flagged:
                det[t] += 1
        suggs_c = check_text(clean_text)
        flags_c = {s.rule for s in suggs_c if s.severity in ('error', 'style')}
        if flags_c:
            clean_flagged += 1
            for r in flags_c:
                clean_flags[r] += 1
        if (i + 1) % 500 == 0:
            print(f'  ... {i+1}/{len(keys)}', flush=True)

    print('\n=== havainto korruptoituneissa (laucetaso) ===')
    for t in sorted(det_tot):
        n = det_tot[t]
        print(f'  {t}: {det[t]}/{n} = {100*det[t]/n:.1f} %')
    print(f'\n=== yli-korjaus puhtaissa kontrolleissa ===')
    print(f'  liputettuja: {clean_flagged}/{len(keys)} = '
          f'{100*clean_flagged/max(1,len(keys)):.2f} %')
    print(f'  saannoittain: {dict(clean_flags.most_common())}')


if __name__ == '__main__':
    main()
