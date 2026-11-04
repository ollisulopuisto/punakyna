#!/usr/bin/env python3
"""Rakenna punakyna-proofreader.oxt (zip). Käyttö: python3 make_oxt.py [out]"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ['punakyna_proofreader.py', 'Linguistic.xcu', 'description.xml',
         'package-description.txt', 'META-INF/manifest.xml']

# paikallinen moottori mukaan pakettiin: ei pip-asennuksia kayttajalle
PKG_DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'punakyna'))
PKG_FILES = ['__init__.py', 'pipeline.py', 'rules.py', 'backend_voikko.py',
             'voikko_gc.py', 'voikko_native.py', 'voikko_compat.py']


def build(out):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            z.write(os.path.join(HERE, rel), rel)
        for name in PKG_FILES:
            z.write(os.path.join(PKG_DIR, name), 'punakyna/' + name)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv) > 1
                else os.path.join(HERE, 'punakyna-proofreader.oxt')))
