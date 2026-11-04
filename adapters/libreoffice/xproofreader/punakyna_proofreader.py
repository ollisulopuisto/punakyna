# -*- coding: utf-8 -*-
"""Punakynä XProofreader - LibreOffice-kieliopintarkistuskomponentti.

Ohut asiakas: välittää virkkeen paikalliselle Punakynä-API:lle
(127.0.0.1:8377) sovelluskohtaisella bearer-tunnuksella
(~/.config/punakyna/tokens/libreoffice; enrollment:
python -m punakyna --enroll-app libreoffice). Vara: perustunnus
~/.config/punakyna/token. Teksti ei lähde koneelta, komponentti ei
kirjoita tekstiä minnekään. API:n ollessa poissa palautetaan
"ei virheitä" - tarkistus ei saa kaataa Writeriä.

Sijainnit: Punakynä-API raportoi Python-koodipisteitä (merkistö);
LibreOffice käyttää UTF-16-yksiköitä. Muunnos tehdään tässä
komponentissa molempiin suuntiin (_slice_utf16 / _utf16_len).

Vain vakio- ja pyuno-kirjastot: komponentti toimii LibreOfficen
omassa Pythonissa ilman asennuksia.

Puuttuva palvelin tai tunnus EI jää hiljaiseksi: kappaleen alkuun
näytetään ohjevirhe, joka kertoo puuttuvan asennusvaiheen
(--serve / --enroll-app). Muut virheet degradaavat hiljaa, ettei
tarkistus kaada Writeriä.
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


def _check(sentence, token):
    body = json.dumps({'text': sentence, 'use_rules': True,
                       'use_spelling': True}).encode('utf-8')
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

        token = _read_token()
        if not token:
            err = setup_error(_MSG_NO_TOKEN)
            aRes.aErrors = (err,) if err else ()
            return aRes

        if (self._setup_fail is not None
                and time.monotonic() - self._setup_fail[1] < _SETUP_FAIL_TTL):
            err = setup_error(self._setup_fail[0])
            aRes.aErrors = (err,) if err else ()
            return aRes

        try:
            suggs = _check(sentence, token)
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
            err.nErrorType = PROOFREADING
            err.aRuleIdentifier = rule_id
            err.aShortComment = s['message'][:100]
            err.aFullComment = s['message']
            err.aSuggestions = tuple(s.get('replacements', [])[:16])
            err.aProperties = ()
            errors.append(err)
        aRes.aErrors = tuple(errors)
        return aRes

    def ignoreRule(self, aRuleIdentifier, aLocale):
        self.ignored_rules.add(aRuleIdentifier)

    def resetIgnoreRules(self):
        self.ignored_rules.clear()


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    PunakynaProofreader, IMPLEMENTATION_NAME, (SERVICE_NAME,))
