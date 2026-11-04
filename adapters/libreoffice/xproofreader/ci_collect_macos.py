#!/usr/bin/env python3
"""CI-apuri (macOS): kokoaa brew-asennetun voikko-pinon bundle-valmisteluun.

Tehdaan GitHub Actions macos-ajajalla (brew saatavilla):
  1. kopioi libvoikko + libhfstospell + NIIDEN reaaliaikaiset dylib-
     riippuvuudet (otool -L -sulkeuma, pois lukien /usr/lib ja /System)
  2. kopioi voikko-fi-sanasto (brew:n libvoikko-formula asentaa sen
     resourcesta $PREFIX/lib/voikko)
  3. hakee KAIKKIEN mukana tulevien komponenttien lahdepaketit
     dist/corresponding-sources/-hakemistoon (pinatut URLit + sha256
     brew:n kaavoista) ja kopioi niiden lisenssitiedostot bundleen
  4. kirjoittaa licenses/SOURCES.txt:n TODELLISILLA versioilla ja
     tarkistussummilla
  5. kutsuu bundle_native.py --platform macos (install_name_tool -korjaukset)

Ei suoriteta kehityskoneella: ajaa vain CI:n macos-latest -ajajalla.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STAGING_LIBS = os.path.join(HERE, '.ci-staging', 'lib')
STAGING_LIC = os.path.join(HERE, '.ci-staging', 'licenses')
DIST_SRC = os.path.normpath(os.path.join(HERE, '..', '..', '..',
                                         'dist', 'corresponding-sources'))
SYSTEM_PREFIXES = ('/usr/lib/', '/System/', '@loader_path/', '@rpath/',
                   '@executable_path/')
BREW_PKGS = ['libvoikko', 'hfstospell']  # sanasto tulee libvoikko-resurssista


def sh(*args):
    return subprocess.run(list(args), check=True, capture_output=True,
                          text=True).stdout.strip()


def brew_prefix(pkg):
    return sh('brew', '--prefix', pkg)


def brew_info(pkg):
    out = sh('brew', 'info', '--json=v2', pkg)
    return json.loads(out)['formulae'][0]


def stage_dylibs():
    """Kopioi voikko-dylibit ja riippuvuussulkeuma staging-hakemistoon."""
    os.makedirs(STAGING_LIBS, exist_ok=True)
    seeds = []
    for pkg in BREW_PKGS:
        libdir = os.path.join(brew_prefix(pkg), 'lib')
        for name in sorted(os.listdir(libdir)):
            if name.endswith('.dylib'):
                seeds.append(os.path.join(libdir, name))
    done = set()
    queue = list(seeds)
    while queue:
        path = queue.pop()
        real = os.path.realpath(path)
        if real in done or not os.path.isfile(real):
            continue
        done.add(real)
        dst = os.path.join(STAGING_LIBS, os.path.basename(real))
        if not os.path.exists(dst):
            shutil.copyfile(real, dst)
        out = sh('otool', '-L', real)
        for line in out.splitlines()[1:]:
            dep = line.strip().split(' ', 1)[0]
            if not dep or dep.startswith(SYSTEM_PREFIXES):
                continue
            if os.path.isfile(dep):
                queue.append(dep)
            else:
                print('VAROITUS: riippuvuutta ei loydy:', dep,
                      file=sys.stderr)
    return sorted(os.listdir(STAGING_LIBS))


def fetch_sources_and_licenses(pkgs_extra):
    """Hae lahdepaketit + poimi lisenssitiedostot. Palauta rivit SOURCES.txt:aan."""
    os.makedirs(DIST_SRC, exist_ok=True)
    os.makedirs(STAGING_LIC, exist_ok=True)
    rows = []
    seen_pkgs = set()
    for pkg in BREW_PKGS + pkgs_extra:
        if pkg in seen_pkgs:
            continue
        seen_pkgs.add(pkg)
        info = brew_info(pkg)
        name = info['name']
        version = info['versions']['stable']
        license_id = info.get('license') or 'tuntematon'
        url = info['urls']['stable']['url']
        sha = info['urls']['stable'].get('checksum', '')
        fn = os.path.basename(url)
        dst = os.path.join(DIST_SRC, fn)
        if not os.path.exists(dst):
            print('ladataan', url)
            urllib.request.urlretrieve(url, dst)
        import hashlib
        got = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
        if sha and got != sha:
            sys.exit('sha256-virhe %s: %s != %s' % (fn, got, sha))
        rows.append((name, version, license_id, url, sha or got))
        # lisenssitiedostot lahdepaketista
        with tempfile.TemporaryDirectory() as td:
            try:
                with tarfile.open(dst) as tf:
                    tf.extractall(td, filter='data')
            except Exception as e:
                print('VAROITUS: purku epaonnistui %s: %s' % (fn, e),
                      file=sys.stderr)
                continue
            for root, _d, files in os.walk(td):
                for f in files:
                    if re.match(r'(?i)^(copying|license|licence|notice)'
                                r'(\.\w+)?$', f):
                        dstname = '%s.%s' % (name, f)
                        shutil.copyfile(os.path.join(root, f),
                                        os.path.join(STAGING_LIC, dstname))
    return rows


def main():
    libs = stage_dylibs()
    print('dylib-kirjastot mukana:', ', '.join(libs))

    # sanasto: libvoikko-formula asentaa voikko-fi-resurssin prefixin alle
    prefix = brew_prefix('libvoikko')
    dict_src = os.path.join(prefix, 'lib', 'voikko')
    if not os.path.isdir(os.path.join(dict_src, '5')):
        alt = os.path.join(prefix, 'share', 'voikko')
        if os.path.isdir(os.path.join(alt, '5')):
            dict_src = alt
        else:
            sys.exit('voikko-fi-sanastoa ei loydy: %s' % dict_src)

    # riippuvuusdylibien omistavat brew-paketit lisenssitietoja varten
    extra = []
    for lib in libs:
        if 'libb2' in lib:
            extra.append('libb2')
        if 'libarchive' in lib:
            extra.append('libarchive')
        if 'libicu' in lib:
            extra.append('icu4c@79')
        if 'libzstd' in lib:
            extra.append('zstd')
        if 'liblz4' in lib:
            extra.append('lz4')
        if 'liblzma' in lib or 'libxz' in lib:
            extra.append('xz')
    rows = fetch_sources_and_licenses(sorted(set(extra)))

    lines = [
        'Punakynä LibreOffice -laajennus: mukana tulevat binäärit ja '
        'niiden lähteet',
        '=' * 74,
        '',
        'Tämä paketti sisältää alla luetellut käännetyt komponentit '
        '(macOS/arm64)',
        'sekä voikko-fi-sanaston. Vastaava lähdekoodi on vapaasti '
        'saatavilla',
        'kustakin osoitteesta; tarkat lähdepaketit toimitetaan '
        'paketin mukana',
        'jakelukanavassa (corresponding-sources/). Paketin täsmällinen',
        'rakennusohje on Punakynä-lähdevarastossa:',
        'adapters/libreoffice/xproofreader/ci_collect_macos.py,',
        'bundle_native.py sekä .github/workflows/build-full-oxt.yml.',
        '',
    ]
    for name, version, license_id, url, sha in rows:
        lines.append('%s %s (%s)' % (name, version, license_id))
        lines.append('  Lähde: %s' % url)
        lines.append('  sha256: %s' % sha)
        lines.append('')
    with open(os.path.join(STAGING_LIC, 'SOURCES.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(lines))

    r = subprocess.run(
        [sys.executable, os.path.join(HERE, 'bundle_native.py'),
         '--platform', 'macos', '--libs', STAGING_LIBS,
         '--dict', dict_src, '--licenses', STAGING_LIC])
    sys.exit(r.returncode)


if __name__ == '__main__':
    main()
