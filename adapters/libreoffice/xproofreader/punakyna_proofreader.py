# -*- coding: utf-8 -*-
"""Punakynä XProofreader - LibreOffice-kieliopintarkistuskomponentti.

Oletusmoottori: PAIKALLINEN - mukana tuleva puhdas-Python-paketti ajaa
libvoikko-moottorin ctypes:n kautta LibreOfficen omassa Pythonissa.
Ei palvelinta, päätettä, tunnuksia eikä rekisteröintiä: asenna .oxt ja
kirjoita. Natiivin libvoikko-taajaman komponentti etsii järjestyksestä:
PUNAKYNA_LIBVOIKKO_PATH, Homebrew-oletukset, LibreOffice.app:n sisältö,
asennettu Voikko-lisäosa (macOS) ja alustan lataaja (voikko_gc.discover_*).

Vara: jos paikallinen moottori ei lataudu JA aiempi palvelinasennus on
olemassa (~/.config/punakyna/token, 0600), käytetään sitä kuten ennen.
Jos kumpikaan ei toimi, kappaleen alkuun näytetään ohjevirhe, joka
nimeää MOLEMMAT epäonnistumiset - vika ei jää näkymättömäksi eikä
varatoiminto vaihda käyttäytymistä hiljaa (valintajärjestys on aina
sama: paikallinen -> palvelin -> ohje). Muut virheet degradaavat
hiljaa, ettei tarkistus kaada Writeriä.

Sijainnit: moottori raportoi Python-koodipisteitä (merkistö);
LibreOffice käyttää UTF-16-yksiköitä. Muunnos tehdään tässä
komponentissa molempiin suuntiin (_slice_utf16 / _utf16_len).

PUNAKYNA_LO_MODE=auto (oletus): paikallinen -> palvelin -> ohje.
PUNAKYNA_LO_MODE=local / =server: pakotettu tila ilman automaattista
vaihtoa (testaus ja kehitys).

Vain vakio- ja pyuno-kirjastot: komponentti toimii LibreOfficen
omassa Pythonissa ilman pip-asennuksia.
"""
import json
import os
import stat
import time
import urllib.error
import urllib.request

import uno
import unohelper

from com.sun.star.linguistic2 import XProofreader, XSupportedLocales
from com.sun.star.lang import XServiceInfo, XServiceDisplayName, Locale
from com.sun.star.text.TextMarkupType import PROOFREADING

import sys as _sys

# .oxt:n sisaan pakattu punakyna/-paketti: LO:n komponenttilataaja ei
# valttamatta lisa laajennuksen hakemistoa sys.path:iin (havaittu LO 7.3).
# Lisataan itse, jotta paikallinen moottori loytyy kaikissa versioissa.
_here_file = globals().get('__file__')
if _here_file:
    _here_dir = os.path.dirname(os.path.abspath(_here_file))
    if _here_dir not in _sys.path:
        _sys.path.insert(0, _here_dir)

def _debug_config():
    try:
        from punakyna import debuglog
        return debuglog.load_config()
    except Exception:
        return None


def _debug_error_type(dbg, default):
    if not dbg:
        return default
    from punakyna import debuglog
    return debuglog.error_type_value(dbg, default)


def _debug_log(dbg, text, start, end, errors):
    if not dbg or not dbg.get('log'):
        return
    try:
        from punakyna import debuglog, __version__
        recs = [{'start': e.nErrorStart, 'length': e.nErrorLength,
                 'type': e.nErrorType, 'rule': e.aRuleIdentifier,
                 'message': e.aFullComment,
                 'suggestions': list(e.aSuggestions),
                 'properties': list(e.aProperties)} for e in errors]
        debuglog.log_call(dbg, text, start, end, recs, __version__)
    except Exception:
        pass


IMPLEMENTATION_NAME = 'org.punakyna.comp.pyuno.PunakynaProofreader'
SERVICE_NAME = 'com.sun.star.linguistic2.Proofreader'
MIN_TOKEN_LEN = 32
# asennusvian ohjevirhe välitetään näin usein uudelleenpalvelinyrityksellä
_SETUP_FAIL_TTL = 15.0

_MSG_NO_TOKEN = ('Punakynä ei ole käytössä: sovellustunnus puuttuu. '
                 'Aja päätteessä: uv run python -m punakyna '
                 '--enroll-app libreoffice')
_MSG_AUTH = ('Punakynä hylkäsi sovellustunnuksen. Rekisteröi uudelleen '
             'päätteessä: uv run python -m punakyna '
             '--enroll-app libreoffice')


def _msg_no_engine(local_err, server_err):
    parts = ['Punakynä: kieliopin tarkistus ei käytössä.']
    if local_err:
        parts.append('Paikallinen moottori ei latautunut: %s.'
                     % str(local_err)[:200])
        parts.append('Asenna joko LibreOfficen Voikko-lisäosa '
                     '(extensions.libreoffice.org - tuplaklikkaa .oxt) '
                     'tai päätteessä: brew install libvoikko voikko-fi - '
                     'ja käynnistä LibreOffice uudelleen.')
    if server_err:
        parts.append('Palvelinvaraus ei myöskään toiminut: %s.'
                     % str(server_err)[:150])
    return ' '.join(parts)


def _msg_server():
    return ('Punakynä-palvelin ei vastaa (127.0.0.1:%d). Käynnistä '
            'päätteessä: uv run python -m punakyna --serve' % _api_port())


def _config_dir():
    return os.path.expanduser(
        os.environ.get('PUNAKYNA_CONFIG', '~/.config/punakyna'))


def _api_port():
    try:
        return int(os.environ.get('PUNAKYNA_PORT', '8377'))
    except ValueError:
        return 8377


def _read_token():
    """Lue tunnus (vain luku - enrollment on erillinen hallintatoimi)."""
    for path in (os.path.join(_config_dir(), 'tokens', 'libreoffice'),
                 os.path.join(_config_dir(), 'token')):
        try:
            st = os.lstat(path)
            if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
                continue
            if stat.S_IMODE(st.st_mode) != 0o600:
                continue
            with open(path, encoding='utf-8') as f:
                tok = f.read().strip()
            if len(tok) >= MIN_TOKEN_LEN:
                return tok
        except OSError:
            continue
    return None


def _utf16_len(s):
    return len(s.encode('utf-16-le', 'surrogatepass')) // 2


def _slice_utf16(text, start, end):
    """LibreOfficen UTF-16-sijainnit -> Python-merkkijono."""
    b = text.encode('utf-16-le', 'surrogatepass')
    return b[2 * start:2 * end].decode('utf-16-le', 'surrogatepass')


def _check(sentence, token, style_profile=None):
    body = json.dumps({'text': sentence, 'use_rules': True,
                       'use_spelling': True, 'style_profile': style_profile}).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:%d/check' % _api_port(), data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))['suggestions']


class PunakynaProofreader(unohelper.Base, XProofreader, XServiceInfo,
                          XServiceDisplayName, XSupportedLocales):
    def __init__(self, ctx, *args):
        # *args: LO antaa alustusargumentteja riippumatta siitä, pyydetäänkö
        self.ctx = ctx
        self.locales = (Locale('fi', 'FI', ''), Locale('fi', '', ''))
        self.ignored_rules = set()
        self._setup_fail = None  # (viesti, monotonic-aikaleima)
        self._mode = None        # 'local' | 'server' | 'fail' | None
        self._token = None
        self._check_text = None
        self._suggestions_as_dicts = None

    # XServiceInfo
    def getImplementationName(self):
        return IMPLEMENTATION_NAME

    def supportsService(self, name):
        return name == SERVICE_NAME

    def getSupportedServiceNames(self):
        return (SERVICE_NAME,)

    # XServiceDisplayName
    def getServiceDisplayName(self, aLocale):
        return 'Punakynä'

    # XSupportedLocales
    def hasLocale(self, aLocale):
        return aLocale.Language == 'fi'

    def getLocales(self):
        return self.locales

    # XProofreader
    def isSpellChecker(self):
        return False

    def doProofreading(self, nDocId, rText, rLocale, nStartOfSentencePos,
                       nSuggestedSentenceEndPos, rProperties):
        aRes = uno.createUnoStruct(
            'com.sun.star.linguistic2.ProofreadingResult')
        aRes.aDocumentIdentifier = nDocId
        aRes.aText = rText
        aRes.aLocale = rLocale
        aRes.nStartOfSentencePosition = nStartOfSentencePos
        aRes.nBehindEndOfSentencePosition = nSuggestedSentenceEndPos
        aRes.nStartOfNextSentencePosition = nSuggestedSentenceEndPos
        aRes.aErrors = ()
        aRes.aProperties = ()
        aRes.xProofreader = self

        sentence = _slice_utf16(rText, nStartOfSentencePos,
                                nSuggestedSentenceEndPos)
        if not sentence.strip():
            return aRes

        def setup_error(message):
            # ohjevirhe kappaleen alkuun: asennusvika ei jää näkymättömäksi
            if nStartOfSentencePos != 0:
                return None
            word = sentence.lstrip().split(None, 1)[0] if sentence.strip()                 else ''
            err = uno.createUnoStruct(
                'com.sun.star.linguistic2.SingleProofreadingError')
            err.nErrorStart = (nStartOfSentencePos
                               + _utf16_len(sentence[:len(sentence)
                                            - len(sentence.lstrip())]))
            err.nErrorLength = max(1, _utf16_len(word[:20]))
            err.nErrorType = PROOFREADING
            err.aRuleIdentifier = 'punakyna.setup'
            err.aShortComment = message[:100]
            err.aFullComment = message
            err.aSuggestions = ()
            err.aProperties = ()
            return err

        if (self._setup_fail is not None
                and time.monotonic() - self._setup_fail[1] < _SETUP_FAIL_TTL):
            err = setup_error(self._setup_fail[0])
            aRes.aErrors = (err,) if err else ()
            return aRes

        from punakyna.style_settings import load_profile
        from dataclasses import asdict
        style_profile = asdict(load_profile())
        from punakyna.style import excluded_text
        if excluded_text(rText):
            style_profile = None  # quotation can span several sentence callbacks
        mode = self._resolve_mode()
        if mode == 'fail':
            err = setup_error(self._setup_fail[0])
            aRes.aErrors = (err,) if err else ()
            return aRes
        if mode == 'local':
            try:
                suggs = self._suggestions_as_dicts(
                    self._check_text(sentence, use_rules=True,
                                     use_spelling=True,
                                     style_profile=style_profile))
                self._setup_fail = None
            except Exception:
                return aRes  # moottorivika kesken ajan: hiljainen degradaatio
        else:
            try:
                suggs = _check(sentence, self._token, style_profile)
                self._setup_fail = None
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    self._setup_fail = (_MSG_AUTH, time.monotonic())
                    err = setup_error(_MSG_AUTH)
                    aRes.aErrors = (err,) if err else ()
                return aRes
            except (urllib.error.URLError, OSError, TimeoutError):
                self._setup_fail = (_msg_server(), time.monotonic())
                err = setup_error(self._setup_fail[0])
                aRes.aErrors = (err,) if err else ()
                return aRes
            except Exception:
                return aRes  # tuntematon virhe: hiljainen degradaatio

        dbg = _debug_config()
        errors = []
        for s in suggs:
            rule_id = 'punakyna.' + s['rule']
            if rule_id in self.ignored_rules:
                continue
            err = uno.createUnoStruct(
                'com.sun.star.linguistic2.SingleProofreadingError')
            err.nErrorStart = (nStartOfSentencePos
                               + _utf16_len(sentence[:s['start']]))
            err.nErrorLength = _utf16_len(sentence[s['start']:s['end']])
            err.nErrorType = _debug_error_type(dbg, PROOFREADING)
            err.aRuleIdentifier = rule_id
            err.aShortComment = s['message'][:100]
            err.aFullComment = s['message']
            err.aSuggestions = (() if dbg and dbg['drop_suggestions']
                                else tuple(s.get('replacements', [])[:16]))
            err.aProperties = ()
            errors.append(err)
        aRes.aErrors = tuple(errors)
        _debug_log(dbg, rText, nStartOfSentencePos, nSuggestedSentenceEndPos,
                   errors)
        return aRes

    def _resolve_mode(self):
        """Valitse moottori deterministisesti: paikallinen -> palvelin.

        Paikallinen moottori ladataan vasta tassa (laiska import), jotta
        komponentin lataus LibreOfficeen ei voi kaatua puuttuvaan
        pakettiin tai natiivikirjastoon - vika nakyi aiemmin vasta
        tarkistettaessa.
        """
        if self._mode is not None:
            return self._mode
        forced = os.environ.get('PUNAKYNA_LO_MODE', 'auto')
        if forced == 'local':
            # pakotettu paikallinen: ei hiljaista varatoimintoa (testit/dev)
            from punakyna import pipeline
            pipeline.get_voikko()
            pipeline._get_gc()
            self._check_text = pipeline.check_text
            self._suggestions_as_dicts = pipeline.suggestions_as_dicts
            self._mode = 'local'
            self._setup_fail = None
            return self._mode
        if forced == 'server':
            token = _read_token()
            if token:
                self._token = token
                self._mode = 'server'
                return self._mode
            self._setup_fail = (_MSG_NO_TOKEN, time.monotonic())
            self._mode = 'fail'
            return self._mode
        local_err = None
        try:
            from punakyna import pipeline
            pipeline.get_voikko()   # natiivikirjasto + sanasto NYT
            pipeline._get_gc()      # kielioppimoottori NYT (sama valimuisti
                                    # kuin check_text:lla)
            self._check_text = pipeline.check_text
            self._suggestions_as_dicts = pipeline.suggestions_as_dicts
            self._mode = 'local'
            self._setup_fail = None
            return self._mode
        except Exception as e:
            local_err = e
        token = _read_token()
        if token:
            self._token = token
            self._mode = 'server'
            return self._mode
        self._setup_fail = (_msg_no_engine(local_err, None),
                            time.monotonic())
        self._mode = 'fail'
        return self._mode

    def ignoreRule(self, aRuleIdentifier, aLocale):
        self.ignored_rules.add(aRuleIdentifier)

    def resetIgnoreRules(self):
        self.ignored_rules.clear()


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    PunakynaProofreader, IMPLEMENTATION_NAME, (SERVICE_NAME,))
