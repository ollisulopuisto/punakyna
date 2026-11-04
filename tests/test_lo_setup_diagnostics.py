# -*- coding: utf-8 -*-
"""XProofreader-komponentin asennusvianäyttö (ilman LibreOfficea).

uno/unohelper/com.sun.star korvataan tynkämoduuleilla ja komponentti
ladataan tiedostosta. Varmistetaan, että puuttuva palvelin tai tunnus
näkyy käyttäjälle ohjevirheenä (ei hiljaista "ei virheitä" -tilaa) ja
etta normaalit virheet toimivat edelleen.
"""
import http.server
import importlib.util
import json
import os
import sys
import threading
import types

import pytest

XPDIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'adapters', 'libreoffice', 'xproofreader')


def _stub_uno(monkeypatch):
    uno = types.ModuleType('uno')
    uno.createUnoStruct = lambda name: types.SimpleNamespace()
    uno.getComponentContext = lambda: None
    unohelper = types.ModuleType('unohelper')

    class Base:
        pass

    class ImplementationHelper:
        def addImplementation(self, *a, **kw):
            pass

    unohelper.Base = Base
    unohelper.ImplementationHelper = ImplementationHelper

    class Locale:
        def __init__(self, lang='', country='', variant=''):
            self.Language = lang
            self.Country = country
            self.Variant = variant

    com = types.ModuleType('com')
    sun = types.ModuleType('com.sun')
    star = types.ModuleType('com.sun.star')
    ling = types.ModuleType('com.sun.star.linguistic2')
    ling.XProofreader = type('XProofreader', (), {})
    ling.XSupportedLocales = type('XSupportedLocales', (), {})
    lang = types.ModuleType('com.sun.star.lang')
    lang.XServiceInfo = type('XServiceInfo', (), {})
    lang.XServiceDisplayName = type('XServiceDisplayName', (), {})
    lang.Locale = Locale
    text = types.ModuleType('com.sun.star.text')
    markup = types.ModuleType('com.sun.star.text.TextMarkupType')
    markup.PROOFREADING = 1

    for name, mod in [('uno', uno), ('unohelper', unohelper),
                      ('com', com), ('com.sun', sun), ('com.sun.star', star),
                      ('com.sun.star.linguistic2', ling),
                      ('com.sun.star.lang', lang),
                      ('com.sun.star.text', text),
                      ('com.sun.star.text.TextMarkupType', markup)]:
        monkeypatch.setitem(sys.modules, name, mod)


def _load(monkeypatch):
    _stub_uno(monkeypatch)
    spec = importlib.util.spec_from_file_location(
        'punakyna_proofreader', os.path.join(XPDIR, 'punakyna_proofreader.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_instance(mod, monkeypatch, tmp_path, token=True):
    cfg = tmp_path / 'cfg'
    (cfg / 'tokens').mkdir(parents=True)
    if token:
        tf = cfg / 'tokens' / 'libreoffice'
        tf.write_text('x' * 64, encoding='utf-8')
        os.chmod(tf, 0o600)
    monkeypatch.setenv('PUNAKYNA_CONFIG', str(cfg))
    return mod.PunakynaProofreader(None)


def _proofread(inst, text, start=0, end=None):
    end = len(text) if end is None else end
    loc = types.SimpleNamespace(Language='fi', Country='FI', Variant='')
    return inst.doProofreading(1, text, loc, start, end, ())


class _StubHandler(http.server.BaseHTTPRequestHandler):
    status = 200
    payload = {'suggestions': []}

    def do_POST(self):
        self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(self.status)
        body = json.dumps(self.payload).encode('utf-8')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def stub_server(monkeypatch):
    srv = http.server.HTTPServer(('127.0.0.1', 0), _StubHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv('PUNAKYNA_PORT', str(srv.server_address[1]))
    yield srv
    srv.shutdown()


def test_missing_token_shows_enroll_hint(monkeypatch, tmp_path):
    mod = _load(monkeypatch)
    inst = _make_instance(mod, monkeypatch, tmp_path, token=False)
    res = _proofread(inst, 'Me olen likaisia.')
    assert len(res.aErrors) == 1
    err = res.aErrors[0]
    assert err.aRuleIdentifier == 'punakyna.setup'
    assert '--enroll-app libreoffice' in err.aFullComment
    assert 'x' * 64 not in err.aFullComment  # ei salaisuuksia viesteissä
    # kesken kappaleen ei spämmätä
    assert _proofread(inst, 'Me olen likaisia.', start=3).aErrors == ()


def test_server_down_shows_serve_hint_and_caches(monkeypatch, tmp_path):
    mod = _load(monkeypatch)
    inst = _make_instance(mod, monkeypatch, tmp_path)
    monkeypatch.setenv('PUNAKYNA_PORT', '1')  # kiinni
    calls = []
    orig = mod._check
    def counting(s, t):
        calls.append(1)
        return orig(s, t)
    monkeypatch.setattr(mod, '_check', counting)
    res = _proofread(inst, 'Me olen likaisia.')
    assert len(res.aErrors) == 1
    assert '--serve' in res.aErrors[0].aFullComment
    assert res.aErrors[0].aRuleIdentifier == 'punakyna.setup'
    # TTL:n sisällä ei uutta palvelinyritystä per virke
    _proofread(inst, 'Toinen virke ilman virhettä.')
    _proofread(inst, 'Kolmas virke vielä.')
    assert len(calls) == 1


def test_auth_rejected_shows_reenroll_hint(monkeypatch, tmp_path, stub_server):
    _StubHandler.status = 401
    mod = _load(monkeypatch)
    inst = _make_instance(mod, monkeypatch, tmp_path)
    res = _proofread(inst, 'Me olen likaisia.')
    assert len(res.aErrors) == 1
    assert '--enroll-app libreoffice' in res.aErrors[0].aFullComment
    _StubHandler.status = 200


def test_normal_errors_and_recovery(monkeypatch, tmp_path, stub_server):
    _StubHandler.status = 200
    _StubHandler.payload = {'suggestions': [
        {'rule': 'PRON_VERB_AGREEMENT', 'message': 'kongruenssi',
         'start': 3, 'end': 7, 'replacements': ['olemme']}]}
    mod = _load(monkeypatch)
    inst = _make_instance(mod, monkeypatch, tmp_path)
    # vanhentunut vianäyttötila: palvelin toimii -> palautuu normaaliksi
    inst._setup_fail = ('vanha vika', 0.0)
    res = _proofread(inst, 'Me olen likaisia.')
    assert inst._setup_fail is None
    assert len(res.aErrors) == 1
    assert res.aErrors[0].aRuleIdentifier == 'punakyna.PRON_VERB_AGREEMENT'
    assert res.aErrors[0].nErrorStart == 3
    assert res.aErrors[0].aSuggestions == ('olemme',)
    _StubHandler.payload = {'suggestions': []}


def test_empty_sentence_stays_quiet(monkeypatch, tmp_path):
    mod = _load(monkeypatch)
    inst = _make_instance(mod, monkeypatch, tmp_path, token=False)
    assert _proofread(inst, '   ').aErrors == ()
