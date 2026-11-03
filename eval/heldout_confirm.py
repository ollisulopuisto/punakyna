"""Vahvistava (confirmatory) erillinen arviointi DaLA Finnish -aineistolla.

Metodologia:
- Kehitysjoukko (dev): testijaon 10 000 ensimmaista paria (seed=42).
  Saantoja on tarkennettu taman joukon virhetarkastelulla 2026-11-03,
  joten SE EI OLE ENAA erillinen aineisto; sen post-fix-luvut ovat
  "tuned/development".
- Vahvistusjoukko (confirm): testijaon parit, jotka eivat ole dev-joukossa
  JA joiden puhdas lause ei esiinny dev-joukon puhtaissa lauseissa
  JA joiden puhdas lause ei esiinny train/validation-jakojen puhtaissa
  lauseissa (ristivuodon tarkistus). Naista otos n=10000 (seed=7).
- Saannot jaadytetty v0.3-committiin; vahvistusajoa EI kayteta virittamiseen.

Mitat (ylla pito operating point, kolme vakavuuskynnyksia):
- havainto: lause liputettu (detection flag; EI korjaus-ehdotusta)
- punakyna korjaus: jokin ehdotuksen korjausvaihtoehdoista tuottaa
  span-korjauksena tasan puhtaan kohdelauseen
- puhtaiden liputusaste (ei "vaaria korjauksia": tyokalu ei korjaa itse)

Moodit: own (vain punakynan saannot), voikko (oikeinkirjoitus + Voikko GC),
combined (kaikki).

Aineisto: schneiderkamplab/dala-fi-audited, config=correction.
Lisenssi: aineiston LICENSE.md: "No blanket replacement license is
asserted. Retain per-record license, source revision, URL, title and
document attribution from provenance." Tietueet: CC-BY-SA-3.0; GFDL.
Aineiston tietueita EI tallenneta tahan repositorioon.

Kaytto: python eval/heldout_confirm.py <data_dir> <mode> [n]
"""
import gzip
import glob
import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from punakyna.pipeline import check_text  # noqa

MODES = {
    'own': dict(use_rules=True, use_spelling=False, use_gc=False),
    'voikko': dict(use_rules=False, use_spelling=True, use_gc=True),
    'combined': dict(use_rules=True, use_spelling=True, use_gc=True),
}
SEVERITY_SETS = {
    'error': {'error'},
    'error+style': {'error', 'style'},
    'all': {'error', 'style', 'info'},
}


def sentence_of(row):
    return row['messages'][0]['content'].split('\n\n', 1)[1].strip()


def load_pairs(pattern, split):
    pairs = {}
    for path in sorted(glob.glob(pattern)):
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            for line in f:
                row = json.loads(line)
                m = row['metadata']
                if m['split'] != split:
                    continue
                p = pairs.setdefault(m['pair_id'], {})
                p[m['variant']] = (sentence_of(row), tuple(m['corruption_types']))
    return pairs


def clean_texts(pattern, split):
    out = set()
    for path in sorted(glob.glob(pattern)):
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            for line in f:
                row = json.loads(line)
                m = row['metadata']
                if m['split'] == split and m['variant'] == 'clean':
                    out.add(sentence_of(row))
    return out


def apply_fix(text, sugg, repl):
    return text[:sugg.start] + repl + text[sugg.end:]


def main():
    data_dir, mode = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    kw = MODES[mode]

    test_pairs = load_pairs(os.path.join(data_dir, '*test*.jsonl.gz'), 'test')
    keys_all = sorted(k for k, v in test_pairs.items()
                      if 'corrupted' in v and 'clean' in v)
    rng = random.Random(42)
    shuffled = keys_all[:]
    rng.shuffle(shuffled)
    dev_keys = set(shuffled[:10000])
    dev_clean = {test_pairs[k]['clean'][0] for k in dev_keys}

    # ristivuoto: testijakojen puhtaat lauseet train/validation-jaoissa
    other_clean = set()
    for split in ('train', 'validation'):
        other_clean |= clean_texts(os.path.join(data_dir, f'*{split}*.jsonl.gz'), split)
    leaked = {t for t in (p['clean'][0] for p in test_pairs.values() if 'clean' in p)
              if t in other_clean}
    print(f'cross-split-vuoto (testin puhdas lause train/validation-jaoissa): '
          f'{len(leaked)}')

    pool = [k for k in keys_all
            if k not in dev_keys
            and test_pairs[k]['clean'][0] not in dev_clean
            and test_pairs[k]['clean'][0] not in other_clean]
    excluded_text_overlap = len(keys_all) - len(dev_keys) - len(pool)
    rng2 = random.Random(7)
    rng2.shuffle(pool)
    keys = pool[:n]
    print(f'vahvistusjoukko: {len(keys)} paria '
          f'(poissuljettu tekstivuodon vuoksi {excluded_text_overlap}, '
          f'dev-joukko erillinen)')

    sev_det = {s: Counter() for s in SEVERITY_SETS}
    sev_tot = Counter()
    sev_clean = {s: 0 for s in SEVERITY_SETS}
    sev_clean_rules = {s: Counter() for s in SEVERITY_SETS}
    exact_fix = 0
    fixable = 0
    for i, k in enumerate(keys):
        corrupt_text, ctypes_ = pairs_ctypes = test_pairs[k]['corrupted']
        clean_text = test_pairs[k]['clean'][0]
        suggs = check_text(corrupt_text, **kw)
        for sev_name, sevs in SEVERITY_SETS.items():
            flagged = {s.rule for s in suggs if s.severity in sevs}
            for t in ctypes_ or ('(none)',):
                if sev_name == 'error+style':
                    sev_tot[t] += 1
                if flagged:
                    sev_det[sev_name][t] += 1
        # punakyna korjaus-ehdotus?
        for s in suggs:
            for r in s.replacements:
                if apply_fix(corrupt_text, s, r) == clean_text:
                    exact_fix += 1
                    break
            else:
                continue
            break
        suggs_c = check_text(clean_text, **kw)
        for sev_name, sevs in SEVERITY_SETS.items():
            flags = [s for s in suggs_c if s.severity in sevs]
            if flags:
                sev_clean[sev_name] += 1
                for s in flags:
                    sev_clean_rules[sev_name][s.rule] += 1
        if (i + 1) % 1000 == 0:
            print(f'  ... {i+1}/{len(keys)}', flush=True)

    print(f'\n=== moodi: {mode} ===')
    print('havainto korruptoituneissa (laucetaso), kynnyksittain:')
    for t in sorted(sev_tot):
        row = '  %-24s n=%d: ' % (t, sev_tot[t])
        for sev_name in ('error', 'error+style', 'all'):
            d = sev_det[sev_name][t]
            row += f'{sev_name}: {d} ({100*d/sev_tot[t]:.1f}%)  '
        print(row)
    print(f'tasmallinen korjaus ehdotettuna: {exact_fix}/{len(keys)} '
          f'= {100*exact_fix/len(keys):.1f}% (kaikki korruptiotyypit)')
    print('puhtaiden kontrollien liputusaste:')
    for sev_name in ('error', 'error+style', 'all'):
        c = sev_clean[sev_name]
        print(f'  {sev_name}: {c}/{len(keys)} = {100*c/len(keys):.2f}% '
              f'saannoittain: {dict(sev_clean_rules[sev_name].most_common(6))}')


if __name__ == '__main__':
    main()
