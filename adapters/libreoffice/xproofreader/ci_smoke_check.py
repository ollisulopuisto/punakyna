#!/usr/bin/env python3
"""CI-ajonaikainen savutesti (macOS-ajaja): pakattu moottori toimii.

Parametri: puretun .oxt:n hakemisto. Homebrew-kirjastot on piilotettu
ennen ajoa (workflow), joten ainoa mahdollinen libvoikko on paketin
mukana tuleva. Ajetaan DYLD_PRINT_LIBRARIES=1:lla ja lokit tarkistetaan
workflow:ssa (mikaan osa ei saa tulla /opt/homebrew:sta).
"""
import sys

sys.path.insert(0, sys.argv[1])

from punakyna import pipeline
from punakyna import voikko_gc

libfile = voikko_gc.discover_libfile()
dictpath = voikko_gc.discover_dict_path(libfile)
print('libfile:', libfile)
print('dict:', dictpath)
assert sys.argv[1] in libfile, 'libvoikko EI tullut paketista: %s' % libfile
assert dictpath and sys.argv[1] in dictpath, \
    'sanasto EI tullut paketista: %s' % dictpath

r = pipeline.check_text('Me olen likaisia.', use_rules=True,
                        use_spelling=True)
suggs = pipeline.suggestions_as_dicts(r)
assert any(s['rule'] == 'PRON_VERB_AGREEMENT'
           and 'olemme' in s['replacements'] for s in suggs), suggs
print('SMOKE OK:', suggs[0]['rule'],
      '%d-%d' % (suggs[0]['start'], suggs[0]['end']),
      suggs[0]['replacements'])
