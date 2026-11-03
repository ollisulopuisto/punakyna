"""Puhtaan kontrolliaineiston liputusaste: UD_Finnish-TDT (Turku TDT).

Aineisto: https://github.com/UniversalDependencies/UD_Finnish-TDT (master)
Lisenssi: CC BY-SA 4.0 (LICENSE.txt mukana latauksessa; provenienssi:
Turku Dependency Treebank, Ginter ym. 2013). Aineistoa EI tallenneta repoon.
Kultaisesti annotoitu yleiskielinen suomi -> lauseiden oletetaan olevan
oikein; liputukset ovat siis yliliputuksia (tai aineiston poikkeamia).

Mittaus on liputusaste, ei tarkkuus; osumien luokittelu on tekijän tarkastelua.

Käyttö: python eval/clean_tdt.py /polku/fi_tdt-ud-test.conllu [/polku/dev...]
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from punakyna.pipeline import check_text
from punakyna.backend_voikko import get_voikko


def sentences(path):
    for line in open(path, encoding='utf-8'):
        if line.startswith('# text = '):
            yield line[len('# text = '):].strip()


def main():
    paths = sys.argv[1:]
    v = get_voikko()
    total = 0
    own = Counter()      # error-taso
    own_all = Counter()  # error+style
    spell = 0
    gc = Counter()
    examples = []
    for p in paths:
        for text in sentences(p):
            total += 1
            suggs = check_text(text, use_rules=True, use_spelling=False)
            own_s = [s for s in suggs if s.rule not in ('SPELL', 'SPELL_UNKNOWN', 'VOIKKO_GC')]
            gc_s = [s for s in suggs if s.rule == 'VOIKKO_GC']
            if any(s.severity == 'error' for s in own_s):
                own['lauseita_error'] += 1
                for s in own_s:
                    if s.severity == 'error':
                        own[s.rule] += 1
            if own_s:
                own_all['lauseita_error_style'] += 1
            if gc_s:
                gc['lauseita'] += 1
                for s in gc_s:
                    gc[s.message[:40]] += 1
                if len(examples) < 12:
                    examples.append((text, [(s.rule, s.message[:60]) for s in suggs]))
            if v.spell(text.replace(' ', '')) is False and False:
                pass
            # oikeinkirjoitus: lause jos jokin sana tuntematon/väärin
            bad = any(v.spell(w) is False for w in text.split() if w.isalpha() and len(w) > 2)
            if bad:
                spell += 1
    print(f'lauseita: {total}')
    print(f'omat säännöt, error-taso: {own["lauseita_error"]} ({own["lauseita_error"]/total*100:.2f} %), säännöittäin: {dict(own)}')
    print(f'omat säännöt, error+style: {own_all["lauseita_error_style"]} ({own_all["lauseita_error_style"]/total*100:.2f} %)')
    print(f'voikko-gc: {gc["lauseita"]} ({gc["lauseita"]/total*100:.2f} %), viesteittäin: {dict(gc)}')
    print(f'oikeinkirjoitus (tuntematon sana): {spell} ({spell/total*100:.2f} %)')
    print('\nesimerkkejä gc-osumista:')
    for t, ss in examples:
        print(' *', t[:90], '->', ss[:3])


if __name__ == '__main__':
    main()
