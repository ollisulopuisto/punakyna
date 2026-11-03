"""Parsitun tason dev/held-mittaus (ks. parse_probe.py:n dokumentaatio)."""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eval.parse_probe import get_nlp, parse_rules  # noqa


class _OneDoc:
    def __init__(self, sent):
        self.sentences = [sent]


def sentences(path):
    for line in open(path, encoding='utf-8'):
        if line.startswith('# text = '):
            yield line[len('# text = '):].strip()


def count_flags(texts):
    nlp = get_nlp()
    flagged = 0
    kinds = {}
    t0 = time.time()
    for i in range(0, len(texts), 40):
        doc = nlp('\n'.join(texts[i:i + 40]))
        for sent in doc.sentences:
            hits = parse_rules(_OneDoc(sent))
            if hits:
                flagged += 1
                for h in hits:
                    kinds[h[0]] = kinds.get(h[0], 0) + 1
    return flagged, kinds, time.time() - t0


def main():
    mode = sys.argv[1]
    if mode == 'tdt':
        if sys.argv[2].endswith('.txt'):
            texts = [l[len('# text = '):].strip() for l in open(sys.argv[2], encoding='utf-8')]
        else:
            texts = list(sentences(sys.argv[2]))
        flagged, kinds, dur = count_flags(texts)
        print(f'TDT puhdas: {flagged}/{len(texts)} = {flagged/len(texts)*100:.2f} % liputettu, saannoittain: {kinds}')
        print(f'latenssi: {len(texts)/dur:.1f} lausetta/s (Linux-hiekkalaatikko, EI Mac-todiste)')
    else:
        phen, split = sys.argv[2], sys.argv[3]
        rows = list(csv.DictReader(open('/tmp/multiblimp_fin.tsv', encoding='utf-8'), delimiter='\t'))
        rows = [r for r in rows if r['phenomenon'].strip() == phen]
        part = rows[0::2] if split == 'dev' else rows[1::2]
        texts = [r['wrong_sen'].replace(' ,', ',').replace(' .', '.') for r in part]
        flagged, kinds, dur = count_flags(texts)
        print(f'korruptio {phen} {split}: {flagged}/{len(texts)} = {flagged/len(texts)*100:.1f} % liputettu {kinds} ({dur:.0f} s)')


if __name__ == '__main__':
    main()
