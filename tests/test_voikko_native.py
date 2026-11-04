# -*- coding: utf-8 -*-
"""ctypes-natiivitausta (voikko_native): toiminta, loytaminen ja pariteetti
pip-sidontaan.

Natiivikirjaston puuttuessa (CI ilman libvoikko-asennusta) moottoritestit
ohitetaan; loytamistestit ovat aina ajettavissa.
"""
import os

import pytest

from punakyna.voikko_gc import discover_dict_path, discover_libfile


def _native_or_skip():
    from punakyna.voikko_native import NativeVoikko
    try:
        return NativeVoikko()
    except Exception as e:
        pytest.skip('natiivinen libvoikko ei ladattavissa: %s' % e)


def test_discovery_honours_env(tmp_path, monkeypatch):
    libdir = tmp_path / 'lib'
    libdir.mkdir()
    libfile = libdir / ('libvoikko.1.dylib' if os.sys.platform == 'darwin'
                        else 'libvoikko.so.1')
    libfile.write_bytes(b'')
    monkeypatch.setenv('PUNAKYNA_LIBVOIKKO_PATH', str(libdir))
    assert discover_libfile() == str(libfile)

    d = tmp_path / 'voikko'
    (d / '5').mkdir(parents=True)
    monkeypatch.setenv('PUNAKYNA_VOIKKO_DICTIONARY_PATH', str(d))
    assert discover_dict_path() == str(d)


def test_native_engine_functional():
    v = _native_or_skip()
    assert v.spell('koira')
    assert not v.spell('asdfqwer')
    assert isinstance(v.suggest('koirra'), list)
    toks = [(t.tokenText, t.tokenType) for t in v.tokens('Me olen likaisia.')]
    assert ('Me', 1) in toks and ('olen', 1) in toks
    # loppufragmentti ilman loppuvalimerkkia on mukana (pip-sidonnan mukana)
    sents = [s.sentenceText for s in v.sentences('Yksi. Kaksi viela')]
    assert sents == ['Yksi. ', 'Kaksi viela']
    an = v.analyze('likaisia')
    assert any(a.get('BASEFORM') == 'likainen' for a in an)


def test_native_pipeline_finds_agreement():
    _native_or_skip()
    import punakyna.backend_voikko as be
    be._VOIKKO = None  # pakota natiivitausta tahan testiin
    be.ACTIVE_BACKEND = None
    from punakyna.pipeline import check_text
    suggs = check_text('Me olen likaisia.')
    hits = [s for s in suggs if s.rule == 'PRON_VERB_AGREEMENT']
    assert hits, [s.rule for s in suggs]
    assert hits[0].start == 3 and hits[0].end == 7
    assert 'olemme' in hits[0].replacements


def test_native_matches_binding():
    """Pariteetti: natiivitausta ja pip-sidonta tuottavat saman tuloksen."""
    libvoikko = pytest.importorskip('libvoikko')
    v_native = _native_or_skip()
    lib_path = os.environ.get('PUNAKYNA_LIBVOIKKO_PATH')
    dict_path = os.environ.get('PUNAKYNA_VOIKKO_DICTIONARY_PATH')
    if lib_path:
        libvoikko.Voikko.setLibrarySearchPath(lib_path)
    kwargs = {'path': dict_path} if dict_path else {}
    try:
        v_bind = libvoikko.Voikko('fi', **kwargs)
    except Exception as e:
        pytest.skip('sidonta ei saa moottoria: %s' % e)
    v_bind.setAcceptUnfinishedParagraphsInGc(True)

    from dataclasses import asdict
    from punakyna.pipeline import _check_text_unlocked
    sents = ['Me olen likaisia.',
             'Tama lause on rikki koska sanat on vaarin ja ja.',
             'Hän meni kouluun ja tuli takaisin.',
             'Suomen kieli on kaunis kieli.']
    for sent in sents:
        a = [asdict(x) for x in _check_text_unlocked(sent, voikko=v_bind)]
        b = [asdict(x) for x in _check_text_unlocked(sent, voikko=v_native)]
        assert a == b, sent
