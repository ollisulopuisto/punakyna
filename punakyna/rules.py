"""Tarkat saannot: virheet, joita libvoikko VFST-morfologialla ei havaita.

Jokainen saanto on tarkoituksella kapea: tarkkuus (vahat vaarat halytykset)
on tarkeampaa kuin herkkyys. Saannot toimivat libvoikko-tokenisoinnin ja
-morfologisen analyysin paalla.
"""
from dataclasses import dataclass, field
from typing import List, Optional

import libvoikko


@dataclass
class Suggestion:
    rule: str
    category: str           # 'spelling' | 'grammar' | 'style'
    severity: str           # 'error' | 'style' | 'info'
    start: int              # merkkisijainti alkuperaisessa tekstissa
    end: int
    message: str
    replacements: List[str] = field(default_factory=list)


@dataclass
class _Tok:
    text: str
    start: int
    end: int
    ttype: object

    @property
    def is_word(self):
        return self.ttype == libvoikko.Token.WORD

    @property
    def lower(self):
        return self.text.lower()


_PIENET_ALKUT = {
    # kuukaudet, viikonpaivat ja vuodenajat kirjoitetaan pienella (Kielitoimiston sanakirja)
    'tammikuu', 'helmikuu', 'maaliskuu', 'huhtikuu', 'toukokuu', 'kesakuu',
    'heinakuu', 'elokuu', 'syyskuu', 'lokakuu', 'marraskuu', 'joulukuu',
    'maanantai', 'tiistai', 'keskiviikko', 'torstai', 'perjantai',
    'lauantai', 'sunnuntai', 'viikko', 'viikonloppu',
    'kevat', 'kesa', 'syksy', 'talvi',
}

_KIELTO = {
    'en', 'et', 'ei', 'emme', 'ette', 'eivat',
    'enko', 'etko', 'eiko', 'emmeko', 'etteko', 'eivatko',
    'ettei', 'etteivat', 'ala', 'alkaa', 'alkoon', 'alkoot',
}

_PRON_KIELTO = {
    'mina': 'en', 'sina': 'et', 'han': 'ei',
    'me': 'emme', 'te': 'ette', 'he': 'eivat',
}


def _analyze(voikko, word, cache):
    if word not in cache:
        cache[word] = voikko.analyze(word)
    return cache[word]


def _baseforms(analyses):
    return {a.get('BASEFORM', '').lower() for a in analyses if a.get('BASEFORM')}


def check_double_word(sent_text, offset, words):
    out = []
    for prev, cur in zip(words, words[1:]):
        if len(cur.text) < 2:
            continue
        if not sent_text[prev.end:cur.start].strip():
            pass
        else:
            continue  # valissa valimerkki (esim. luettelo "Concorde, Concorde Nova")
        if cur.text[:1].isupper():
            continue  # toistuva nimi ("Díaz Díaz", "Sigue Sigue Sputnik")
        if prev.text[:1].isupper() and prev.start > 0:
            continue  # tieteellinen kaksinimitys ("Histrionicus histrionicus")
        if prev.lower == cur.lower:
            out.append(Suggestion(
                rule='DOUBLE_WORD', category='grammar', severity='error',
                start=offset + cur.start, end=offset + cur.end,
                message=f'Sana "{cur.text}" toistuu peräkkäin.',
                replacements=[]))
    return out


_NEG_SG = {'en', 'et', 'ei', 'enko', 'etko', 'eiko', 'älä', 'ettei'}
_NEG_PL = {'emme', 'ette', 'eivät', 'emmekö', 'ettekö', 'eivätkö',
           'älkää', 'etteivät'}


def _connegative_ok(analyses, plural):
    """Onko sanamuoto kelvollinen kieltoverbin liittomuoto?

    Voikko-fi:n FST-merkinnat: [Tk] = konnegatiivi/imperatiivimuoto,
    [Ll][Ru] = nut/nyt-partisiippi (mennyt aika: yks. en/et/ei tiennyt,
    mon. emme/ette/eivat tienneet), [Te]/[Tm] yks. 3. pers. =
    konditionaalin/potentiaalin konnegatiivi (ei tulisi / ei tiennee).
    """
    for a in analyses:
        fst = a.get('FSTOUTPUT') or ''
        if '[Tk]' in fst:
            return True
        if (a.get('CLASS') == 'teonsana' and '[Tt]' in fst
                and a.get('NEGATIVE') in ('true', 'both')):
            return True  # finiittimuoto, joka voi olla konnegatiivi ("ei pelaa")
        if '[Ll][Rt]' in fst:
            return True  # menneen ajan passiivin konnegatiivi ("ei saatu")
        if a.get('PERSON') == '4' and a.get('NEGATIVE') == 'true':
            return True  # preesensin passiivin konnegatiivi ("ei asuteta")
        if a.get('CLASS') == 'laatusana' and '[Ll][Ru]' in fst:
            if ('[Nm]' in fst) == plural:
                return True
        if (a.get('MOOD') in ('conditional', 'potential')
                and a.get('PERSON') in ('3', '4')):
            return True
    return False


def _verbish(analyses):
    for a in analyses:
        if a.get('CLASS') == 'teonsana':
            return True
        if a.get('CLASS') == 'laatusana' and '[Ll][R' in (a.get('FSTOUTPUT') or ''):
            return True
    return False


def _main_verb_candidate(analyses):
    """Voiko muoto olla kieltoverbin paatekohteena?

    Infiniitit ([Tn]) ja preesensin partisiipit ([Ll][Rv], esim. 'vastaavien')
    eivat lopeta etsintaa: ne ovat adverbiaali- tai adjektiivikaytossa
    ('ei valttamatta ole', 'ei muiden vastaavien elokuvien tapaan').
    """
    for a in analyses:
        fst = a.get('FSTOUTPUT') or ''
        if a.get('CLASS') == 'teonsana' and ('[Tt]' in fst or '[Tk]' in fst):
            return True
        if a.get('PERSON') == '4':
            return True
        if a.get('CLASS') == 'laatusana' and ('[Ll][Ru]' in fst or '[Ll][Rt]' in fst):
            return True
    return False


def check_negation(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        low = tok.lower
        if low not in _NEG_SG and low not in _NEG_PL:
            continue
        plural = low in _NEG_PL
        for nxt in words[i + 1:i + 4]:
            if ',' in sent_text[tok.end:nxt.start]:
                break  # lauseenosa loppuu pilkkuun ("ei hevonen, oli ...")
            analyses = _analyze(voikko, nxt.text, cache)
            if not _verbish(analyses):
                continue
            if not _main_verb_candidate(analyses):
                continue
            if not _connegative_ok(analyses, plural):
                out.append(Suggestion(
                    rule='NEG_CONNEGATIVE', category='grammar', severity='error',
                    start=offset + nxt.start, end=offset + nxt.end,
                    message=('Kieltoverbin liittomuoto: kieltoverbin kanssa '
                             'käytetään konnegatiivia (esim. "en tiennyt", '
                             '"emme tienneet", ei "en tienneet").'),
                    replacements=[]))
            break
    return out


def check_negation_agreement(sent_text, offset, words):
    out = []
    for prev, cur in zip(words, words[1:]):
        want = _PRON_KIELTO.get(prev.lower)
        if want and cur.lower in _KIELTO and cur.lower != want:
            out.append(Suggestion(
                rule='NEG_NUMBER', category='grammar', severity='error',
                start=offset + cur.start, end=offset + cur.end,
                message=(f'Kieltosanan kongruenssi: pronominin "{prev.text}" '
                         f'kanssa käytetään muotoa "{want}".'),
                replacements=[want]))
    return out


def _olla_sg(verb_an):
    return any(a.get('BASEFORM') == 'olla' and a.get('NUMBER') == 'singular'
               and a.get('PERSON') == '3' and a.get('MOOD') == 'indicative'
               and a.get('TENSE') == 'present_simple' for a in verb_an)


def _olla_pl(verb_an):
    return any(a.get('BASEFORM') == 'olla' and a.get('NUMBER') == 'plural'
               and a.get('PERSON') == '3' and a.get('MOOD') == 'indicative'
               and a.get('TENSE') == 'present_simple' for a in verb_an)


def _nom_pl_noun(analyses):
    return any(a.get('CLASS') == 'nimisana' and a.get('NUMBER') == 'plural'
               and a.get('SIJAMUOTO') == 'nimento' for a in analyses)


def _nom_sg_noun(analyses):
    return any(a.get('CLASS') == 'nimisana' and a.get('NUMBER') == 'singular'
               and a.get('SIJAMUOTO') == 'nimento' for a in analyses)


def _has_number(analyses, number):
    return any(a.get('CLASS') == 'nimisana' and a.get('NUMBER') == number
               for a in analyses)


def _passive_participle_ahead(voikko, cache, words, i, sent_text):
    """Loytyyko "on"-muotoa seuraavilta token-alueelta passiivin
    VA- tai TU-partisiippi ennen pilkkua/pistettä."""
    for w in words[i + 1:i + 8]:
        frag = sent_text[words[i].end:w.start]
        if ',' in frag or '.' in frag:
            break
        for a in _analyze(voikko, w.text, cache):
            if a.get('PARTICIPLE') in ('present_passive', 'past_passive'):
                return True
    return False


def check_olla_agreement(sent_text, offset, words, voikko, cache):
    """Kapea kongruenssisaanto: nominatiivinen subjekti valittomasti ennen on/ovat.

    Eksistentiaalilause ("Poydalla on kirjat") ei osu, koska sina verbi
    edeltaa subjektia. Monikon partitiivi ("menoja on") ei osu.
    """
    out = []
    for i, (prev, cur) in enumerate(zip(words, words[1:])):
        verb_an = [a for a in _analyze(voikko, cur.text, cache)
                   if a.get('CLASS') == 'teonsana']
        if not verb_an:
            continue
        if ',' in sent_text[prev.end:cur.start]:
            continue  # inversio/luettelo ("nämä ääripäät, on se, että ...")
        if prev.lower == 'kaikki':
            continue  # "jotka kaikki ovat": viittaa monikkoon
        # koordinoitu subjekti ("lait ja lakien valvonta ovat",
        # "hyväksikäyttö, pahoinpitely tai heitteillejättö ovat"):
        # katso enintaan 5 sanaa taaksepain, pysahdy finiittiverbiin
        for back in words[max(0, i - 5):i][::-1]:
            if any(a.get('CLASS') == 'teonsana' and '[Tt]' in (a.get('FSTOUTPUT') or '')
                   for a in _analyze(voikko, back.text, cache)):
                break
            if back.lower in ('ja', 'sekä', 'tai'):
                break
        else:
            back = None
        if back is not None and back.lower in ('ja', 'sekä', 'tai'):
            continue
        prev_an = _analyze(voikko, prev.text, cache)
        if any(a.get('CLASS') in ('sukunimi', 'etunimi', 'paikannimi')
               for a in prev_an):
            continue  # esim. Yhdysvallat: monikkomuoto, yksikkokongruenssi
        if any(a.get('CLASS') != 'nimisana' for a in prev_an):
            continue  # pronominin ym. sijamuodot eivat ole subjektiarvioita
        if not prev_an:
            continue
        if prev.text.lower().endswith(('ni', 'si', 'nsa', 'nsä', 'mme', 'nne')):
            continue  # possessiivisuffiksi yhdistaa numerot ("kirjeensä ovat")
        if prev.text[:1].isupper() and prev is not words[0]:
            # monisanainen kollektiivierisnimi ("Helsingin Sanomat on
            # varovainen", "Arabiemiraatit torjui") - yksikkokongruenssi OK
            # (VISK §1284c, Kielikello: morfosyntaksi ja kielenhuolto)
            continue
        if (_olla_sg(verb_an) and _nom_pl_noun(prev_an)
                and not _has_number(prev_an, 'singular')):
            # VISK §1581: nesessiivirakenne ("Turvavyot on pidettava",
            # "Avaimet on palautettava") ja passiivin perfekti
            # ("Nayttelijat on laitettu huutamaan") eivat kongruoitu
            # subjektin luvussa -> ei osumaa.
            if _passive_participle_ahead(voikko, cache, words, i, sent_text):
                continue
            out.append(Suggestion(
                rule='SV_AGREEMENT', category='grammar', severity='error',
                start=offset + cur.start, end=offset + cur.end,
                message=('Kongruenssi: monikollinen subjekti ("%s") vaatii '
                         'monikollisen verbin (esim. "ovat").' % prev.text),
                replacements=['ovat']))
        elif (_olla_pl(verb_an) and _nom_sg_noun(prev_an)
              and not _has_number(prev_an, 'plural')):
            out.append(Suggestion(
                rule='SV_AGREEMENT', category='grammar', severity='error',
                start=offset + cur.start, end=offset + cur.end,
                message=('Kongruenssi: yksiköllinen subjekti ("%s") vaatii '
                         'yksiköllisen verbin (esim. "on").' % prev.text),
                replacements=['on']))
    return out


def check_lowercase_names(sent_text, offset, words, voikko, cache):
    """Kuukausi/viikonpaiva/vuodenaika isolla alkukirjaimella lauseen sisalla."""
    out = []
    first = True
    for tok in words:
        is_sent_start = first
        first = False
        if not tok.text[:1].isupper():
            continue
        if is_sent_start:
            continue
        analyses = _analyze(voikko, tok.text, cache)
        # erisnimeksi tulkittavaa sanaa ei "oikaista" (esim. sukunimi Syksy)
        if any(a.get('CLASS') in ('sukunimi', 'etunimi', 'paikannimi')
               for a in analyses):
            continue
        if _baseforms(analyses) & _PIENET_ALKUT:
            out.append(Suggestion(
                rule='CAP_COMMON_NOUN', category='style', severity='style',
                start=offset + tok.start, end=offset + tok.end,
                message=('Aakkosellisuus: kuukausien, viikonpäivien ja '
                         'vuodenaikojen nimet kirjoitetaan pienellä '
                         'alkukirjaimella. Jos sana on erisnimi (esim. '
                         'sukunimi), älä muuta.'),
                replacements=[tok.lower]))
    return out


_PRON_VERB_REQ = {
    # asemosana -> vaadittu (persoona, luku) finiittiverbille
    'minä': ('1', 'singular'), 'mä': ('1', 'singular'),
    'sinä': ('2', 'singular'), 'sä': ('2', 'singular'),
    'hän': ('3', 'singular'),
    'me': ('1', 'plural'), 'te': ('2', 'plural'), 'he': ('3', 'plural'),
}
# Puhekielessä 1. persoonan monikko korvautuu passiivin finiittimuodolla
# ("me ollaan", "me mennään", "me oltiin") - VISK, puhekielen kongruenssi.
# Hyväksytään vain "me":n jälkeen; "he/te + passiivi" jätetään arvioimatta.
_PRON_PASSIVE_OK = {'me'}

_OLLA_PARADIGM = {
    ('indicative', 'present_simple', '1', 'singular'): 'olen',
    ('indicative', 'present_simple', '2', 'singular'): 'olet',
    ('indicative', 'present_simple', '3', 'singular'): 'on',
    ('indicative', 'present_simple', '1', 'plural'): 'olemme',
    ('indicative', 'present_simple', '2', 'plural'): 'olette',
    ('indicative', 'present_simple', '3', 'plural'): 'ovat',
    ('indicative', 'past_imperfective', '1', 'singular'): 'olin',
    ('indicative', 'past_imperfective', '2', 'singular'): 'olit',
    ('indicative', 'past_imperfective', '3', 'singular'): 'oli',
    ('indicative', 'past_imperfective', '1', 'plural'): 'olimme',
    ('indicative', 'past_imperfective', '2', 'plural'): 'olitte',
    ('indicative', 'past_imperfective', '3', 'plural'): 'olivat',
}


def _fold(w):
    return w.replace('ä', 'a').replace('ö', 'o')


_NEG_CLITICS = ('kaan', 'ko', 'ka', 'han', 'pa', 's')  # aaneisfoldattuna


def _neg_base(w):
    """Kieltoverbi + kliitit: "eivätkä" -> "eivat", "eikös" -> "eiko"."""
    f = _fold(w)
    for suf in _NEG_CLITICS:
        if f.endswith(suf) and f[:-len(suf)] in _KIELTO:
            return f[:-len(suf)]
    return f


def check_pron_verb_agreement(sent_text, offset, words, voikko, cache):
    """Asemosana + välittömästi seuraava finiittiverbi: persoona/luku.

    Tarkkuus ensin: vain vierekkäiset sanat (kaukana oleva subjekti vaatii
    jäsennystason). Tuntematonta sanaa tai ei-verbianalyysia ei liputeta
    (puhekieliset "mä oon" -muodot jäävät rauhaan). Puhekielinen
    "me + passiivi" hyväksytään. Kieltoverbit kuuluvat NEG_NUMBER-säännölle.
    """
    out = []
    for i, (prev, cur) in enumerate(zip(words, words[1:])):
        req = _PRON_VERB_REQ.get(prev.lower)
        if not req:
            continue
        if cur.lower in _KIELTO:
            continue
        all_an = _analyze(voikko, cur.text, cache)
        verb_an = [a for a in all_an if a.get('CLASS') == 'teonsana'
                   and a.get('MOOD') in ('indicative', 'potential',
                                         'conditional', 'imperative')]
        if not verb_an:
            continue
        if len(verb_an) < len(all_an):
            continue  # monitulkintainen (esim. "niitä" asemosana): ohita
        if any(a.get('NEGATIVE') in ('true', 'both', True) for a in verb_an) \
                and any(_neg_base(w.lower) in _KIELTO
                        for w in words[max(0, i - 3):i]):
            continue  # konnegatiivi: kongruenssi kieltoverbiin (NEG-saannot)
        personal = [(a.get('PERSON'), a.get('NUMBER')) for a in verb_an
                    if a.get('PERSON') in ('1', '2', '3')]
        if not personal:
            continue  # pelkkä passiivi: ok "me":lle, muille arvioimatta
        if req in personal:
            continue
        found = personal[0]
        luku_req = 'monikon' if req[1] == 'plural' else 'yksikön'
        luku_found = 'yksikön' if found[1] == 'singular' else 'monikon'
        repl = []
        base = verb_an[0].get('BASEFORM')
        if base == 'olla':
            form = _OLLA_PARADIGM.get((verb_an[0].get('MOOD'),
                                       verb_an[0].get('TENSE'),
                                       req[0], req[1]))
            if form:
                repl = [form]
        out.append(Suggestion(
            rule='PRON_VERB_AGREEMENT', category='grammar', severity='error',
            start=offset + cur.start, end=offset + cur.end,
            message=(f'Persoonakongruenssi: pronominin "{prev.text}" kanssa '
                     f'verbin tulee olla {luku_req} {req[0]}. persoonassa, '
                     f'mutta "{cur.text}" on {luku_found} {found[0]}. '
                     f'persoonaa.'),
            replacements=repl))
    return out


def run_rules(sent_text, offset, tokens, voikko, cache):
    words = [t for t in tokens if t.is_word]
    out = []
    out += check_double_word(sent_text, offset, words)
    out += check_negation(sent_text, offset, words, voikko, cache)
    out += check_negation_agreement(sent_text, offset, words)
    out += check_olla_agreement(sent_text, offset, words, voikko, cache)
    out += check_pron_verb_agreement(sent_text, offset, words, voikko, cache)
    out += check_lowercase_names(sent_text, offset, words, voikko, cache)
    return out
