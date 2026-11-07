#!/usr/bin/env python3
"""Kirjoita LibreOfficen laajennuspaivityksen syotetiedosto punakyna.update.xml.

Kaytto: python3 make_update_xml.py TAG [out]
Versio luetaan description.xml:sta. Tiedosto liitetaan julkaistun GitHub-
julkaisun liitteeksi (osoite on description.xml:n update-information-src),
OXT-tiedosto haetaan samasta julkaisusta. Vain julkaistut julkaisut kay:
luonnos- ja esijulkaisut eivat nay /releases/latest-osoitteessa."""
import os
import re
import sys
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = 'ollisulopuisto/punakyna'
OXT = 'punakyna-full-macos.oxt'


def read_description(path=None):
    text = open(path or os.path.join(HERE, 'description.xml'), encoding='utf-8').read()
    ident = re.search(r'<identifier value="([^"]+)"', text).group(1)
    version = re.search(r'<version value="([^"]+)"', text).group(1)
    return ident, version


def build(tag, ident=None, version=None):
    if ident is None or version is None:
        ident, version = read_description()
    url = 'https://github.com/%s/releases/download/%s/%s' % (REPO, tag, OXT)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<description xmlns="http://openoffice.org/extensions/update/2006"\n'
        '    xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        ' <identifier value=%s/>\n'
        ' <version value=%s/>\n'
        ' <update-download>\n'
        '  <src xlink:href=%s/>\n'
        ' </update-download>\n'
        '</description>\n'
    ) % (quoteattr(ident), quoteattr(version), quoteattr(url))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'punakyna.update.xml')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(build(sys.argv[1]))
    print(out)
