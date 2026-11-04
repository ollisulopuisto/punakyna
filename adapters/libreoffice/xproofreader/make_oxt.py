#!/usr/bin/env python3
"""Rakenna punakyna-proofreader.oxt (zip). Käyttö: python3 make_oxt.py [out]"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ['punakyna_proofreader.py', 'Linguistic.xcu', 'description.xml',
         'package-description.txt', 'META-INF/manifest.xml']


def build(out):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            z.write(os.path.join(HERE, rel), rel)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv) > 1
                else os.path.join(HERE, 'punakyna-proofreader.oxt')))
