"""Tarkat saannot: virheet, joita libvoikko VFST-morfologialla ei havaita.

Jokainen saanto on tarkoituksella kapea: tarkkuus (vahat vaarat halytykset)
on tarkeampaa kuin herkkyys. Saannot toimivat libvoikko-tokenisoinnin ja
-morfologisen analyysin paalla.
"""
import re
from dataclasses import dataclass, field
from typing import List

from .voikko_compat import Token


@dataclass
class Suggestion:
    rule: str
    category: str           # 'spelling' | 'grammar' | 'style'
    severity: str           # 'error' | 'warning' | 'style' | 'info'
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
        return self.ttype == Token.WORD

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
        # Suorituskyky: Verrataan sanoja ensin. Lähes kaikki peräkkäiset sanat
        # ovat eri sanoja (prev.lower != cur.lower), joten vältetään turha
        # osamerkkijonojen leikkely (sent_text[prev.end:cur.start].strip()) ja
        # isupper()-tarkistukset valtaosalle sanapareista.
        if prev.lower != cur.lower:
            continue
        if len(cur.text) < 2:
            continue
        if sent_text[prev.end:cur.start].strip():
            continue  # valissa valimerkki (esim. luettelo "Concorde, Concorde Nova")
        if cur.text[:1].isupper():
            continue  # toistuva nimi ("Díaz Díaz", "Sigue Sigue Sputnik")
        if prev.text[:1].isupper() and prev.start > 0:
            continue  # tieteellinen kaksinimitys ("Histrionicus histrionicus")
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


# Olla-verbin preesensin 3. persoonan muodot (on/ovat).
# check_olla_agreement tarkistaa ainoastaan näiden kongruenssin
# nominatiivisubjektin kanssa; muiden sanojen analyysi ohitetaan varhaisella
# poistumisella CPU-kuorman ja libvoikko-kutsujen vähentämiseksi.
_OLLA_3RD_PRES = {'on', 'ovat'}


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
        # Suorituskykyoptimointi: sääntö koskee vain preesensin 3. persoonan
        # muotoja ("on" tai "ovat"). Ohitetaan morfologinen analyysi heti,
        # jos sana ei ole kumpikaan näistä.
        if cur.lower not in _OLLA_3RD_PRES:
            continue
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


# Yksikon nominatiivisubjekti + monikon 3. persoonan verbi ("Lapsi leikkivät").
# VISK §1267-1270 (kongruenssi): finiittiverbi kongruoi subjektin kanssa
# luvussa. Vain suunta yksikko -> monikkoverbi tarkistetaan: monikkosubjekti +
# yksikkoverbi ("lapset leikkii") on puhekielen yleinen muoto (VISK §1272
# kuvaa puhekielen persoonajarjestelmaa), joten sita ei liputeta.
# On/ovat kuuluu check_olla_agreement-saannolle.
_ORDINAL_BEFORE = re.compile(r'\d+\.\s*$')
_COORD_BEFORE = re.compile(r'(?:^|\s)(?:ja|sekä|tai|eli|että)(?:\s|$)')


def _sg_nom_only(analyses):
    return bool(analyses) and all(
        a.get('CLASS') == 'nimisana' and a.get('NUMBER') == 'singular'
        and a.get('SIJAMUOTO') == 'nimento' for a in analyses)


def _finite_3pl(analyses):
    return any(a.get('CLASS') == 'teonsana' and a.get('PERSON') == '3'
               and a.get('NUMBER') == 'plural'
               and a.get('MOOD') in ('indicative', 'conditional', 'potential')
               for a in analyses)


def check_sg_subject_plural_verb(sent_text, offset, words, voikko, cache, before=''):
    out = []
    for i, (prev, cur) in enumerate(zip(words, words[1:])):
        if cur.lower in _OLLA_3RD_PRES or len(cur.text) < 5:
            continue
        if not cur.lower.endswith(('vat', 'vät', 'ivat', 'ivät', 'isivat', 'isivät')):
            continue  # varhainen poistuminen: monikon 3. persoonan paate
        if sent_text[prev.end:cur.start].strip():
            continue  # valimerkki valissa
        if prev.lower in ('kaikki', 'moni', 'joku', 'jokainen', 'kukaan', 'mikään'):
            continue
        if prev.text[:1].isupper() and prev is not words[0]:
            continue  # kollektiivinen erisnimi
        if prev is words[0] and prev.text[:1].islower():
            continue  # virkkeen alku pienella: katkennut "3. ja 5. divisioona" -virke
        # koordinoitu tai yhteinen subjekti ("Pekka ja Liisa", "poika sekä tytto")
        coord = False
        for back in words[max(0, i - 5):i][::-1]:
            if back.lower in ('ja', 'sekä', 'tai', 'eli', 'että', 'vaan', 'mutta', 'sekä'):
                coord = True
                break
            if any(a.get('CLASS') == 'teonsana' and '[Tt]' in (a.get('FSTOUTPUT') or '')
                   for a in _analyze(voikko, back.text, cache)):
                break
        if not coord and _COORD_BEFORE.search(sent_text[max(0, prev.start - 30):prev.start]):
            coord = True  # esim. "34. ja 50. Armeijakunta hyokkasivat" (numerot eivat ole sanoja)
        if not coord and _ORDINAL_BEFORE.search((before + sent_text)[:len(before) + prev.start]):
            coord = True  # lauseraja jakaa "3. ja 5. divisioona" (jarjestysluvun piste)
        if coord:
            continue
        verb_an = _analyze(voikko, cur.text, cache)
        if not _finite_3pl(verb_an):
            continue
        if any(a.get('BASEFORM') == 'olla' for a in verb_an):
            continue  # kopula: sopii predikatiivin kanssa ("tekija olivat ...")
        prev_an = _analyze(voikko, prev.text, cache)
        if not _sg_nom_only(prev_an):
            continue
        if any(a.get('POSSESSIVE') for a in prev_an):
            continue  # possessiivisuffiksi yhdistaa numerot ("kirjansa ovat")
        if any(a.get('CLASS') in ('sukunimi', 'etunimi', 'paikannimi')
               for a in prev_an):
            continue
        out.append(Suggestion(
            rule='SV_NUMBER_NONOLLA', category='grammar', severity='warning',
            start=offset + cur.start, end=offset + cur.end,
            message=('Kongruenssi: yksiköllinen subjekti ("%s") ja monikon '
                     '3. persoonan verbi "%s". Tarkista luku.' % (prev.text, cur.text)),
            replacements=[]))
    return out


# Numeraali (nominatiivi) + laskettava substantiivi: "kolme lasta", ei "kolme lapsi".
# VISK §789 ("Viisi lasta ja viidellä lapsella"): yksikon nominatiivissa tai
# partitiivissa olevan numeraalin kanssa laskettava on yksikon partitiivissa;
# muissa sijoissa numeraali ja substantiivi kongruoivat. Rajattu: perusluvut
# 2-19 omina sanoinaan, seuraava sana vain yksikon nominatiivina analysoituva
# yleisnimi. "kuusi" ohitetaan (kuusi = myos puu), samoin sata/tuhat ym.
_NUM_NOM = {
    'kaksi', 'kolme', 'neljä', 'viisi', 'seitsemän', 'kahdeksan', 'yhdeksän',
    'kymmenen', 'yksitoista', 'kaksitoista', 'kolmetoista', 'neljätoista',
    'viisitoista', 'kuusitoista', 'seitsemäntoista', 'kahdeksantoista',
    'yhdeksäntoista',
}


def check_numeral_noun_case(sent_text, offset, words, voikko, cache):
    out = []
    for i, (prev, cur) in enumerate(zip(words, words[1:])):
        if prev.lower not in _NUM_NOM:
            continue
        if sent_text[prev.end:cur.start].strip():
            continue  # valimerkki valissa ("kaksi, kolme")
        if cur.text[:1].isupper():
            continue  # nimi ("Kolme Viisasta")
        if i > 0 and words[i - 1].lower in ('kello', 'klo', 'numero', 'luku', 'sivu',
                                            'kohta', 'pykälä', 'vuonna', 'ja', 'tai', 'sekä'):
            continue  # kellonaika, numero + nimike, luettelo
        cur_an = _analyze(voikko, cur.text, cache)
        if not _sg_nom_only(cur_an):
            continue
        if any(a.get('POSSESSIVE') for a in cur_an):
            continue
        if any(a.get('CLASS') in ('sukunimi', 'etunimi', 'paikannimi') for a in cur_an):
            continue
        if cur.lower in _NUM_NOM or cur.lower in ('sata', 'tuhat', 'miljoona', 'miljardi'):
            continue
        out.append(Suggestion(
            rule='NUM_NOUN_CASE', category='grammar', severity='warning',
            start=offset + cur.start, end=offset + cur.end,
            message=('Numeraalin "%s" jälkeen laskettava on yksikön partitiivissa '
                     '(esim. "kolme lasta"), ei nominatiivissa.' % prev.text),
            replacements=[]))
    return out


# Laatusanaattribuutti + substantiivi nominatiivissa: luku kongruoi ("isot talot",
# ei "isot talo", ei "iso talot"). VISK §1302 (etumääritteiden kongruenssi:
# luvussa ja sijassa) ja §582. Rajattu: kaikki molempien sanojen analyysit ovat
# yksiselitteisesti nominatiivissa ja luvuiltaan eri, ei erisnimia, ei
# määräilmauksia, ei valimerkkia valissa.
_ATTR_SKIP = {
    'moni', 'monet', 'usea', 'useat', 'harva', 'harvat', 'muu', 'muut',
    'eri', 'eräs', 'eräät', 'toinen', 'toiset', 'kumpikin', 'molemmat',
    'sellainen', 'sellaiset', 'tällainen', 'tällaiset', 'kaikki',
}


def _only_adj_number(analyses):
    """Palauttaa 'singular'/'plural', jos kaikki analyysit ovat laatusanan nominatiivia samassa luvussa."""
    if not analyses:
        return None
    nums = set()
    for a in analyses:
        if a.get('CLASS') not in ('laatusana', 'nimisana_laatusana') \
                or a.get('SIJAMUOTO') != 'nimento' or a.get('PARTICIPLE'):
            return None  # partisiipit (nähnyt, ollut) jätetään: ne eivät ole attribuutteja
        nums.add(a.get('NUMBER'))
    return nums.pop() if len(nums) == 1 else None


def _only_noun_number(analyses):
    if not analyses:
        return None
    nums = set()
    for a in analyses:
        if a.get('CLASS') != 'nimisana' or a.get('SIJAMUOTO') != 'nimento':
            return None
        if a.get('POSSESSIVE'):
            return None
        nums.add(a.get('NUMBER'))
    return nums.pop() if len(nums) == 1 else None


def check_attribute_agreement(sent_text, offset, words, voikko, cache):
    out = []
    for i, (adj, noun) in enumerate(zip(words, words[1:])):
        if sent_text[adj.end:noun.start].strip():
            continue
        if noun.text[:1].isupper() or (adj.text[:1].isupper() and i > 0):
            continue  # nimet jatetaan; lauseen ensimmainen sana saa olla isolla
        if adj.lower in _ATTR_SKIP:
            continue
        if noun.lower in ('itse', 'toisaalta', 'kyllä'):
            continue  # adverbimaiset sanat: "suomalaiset itse"
        # Suorituskyky: Varmistetaan ensin, että ensimmäinen sana on attribuuttina
        # toimiva laatusana (a_num). Valtaosa peräkkäisistä sanoista tekstissä
        # ei ala laatusanalla, joten ohitetaan toisen sanan kallis analyysi
        # (_analyze) ja _only_noun_number varhaisella poistumisella.
        a_an = _analyze(voikko, adj.text, cache)
        a_num = _only_adj_number(a_an)
        if not a_num:
            continue
        n_an = _analyze(voikko, noun.text, cache)
        n_num = _only_noun_number(n_an)
        if not n_num or a_num == n_num:
            continue
        if any(a.get('CLASS') in ('sukunimi', 'etunimi', 'paikannimi') for a in n_an):
            continue
        # seuraava sana nimisana nominatiivissa: yhdyssana/luettelo, ei arvioida
        if i + 2 < len(words) and not sent_text[noun.end:words[i + 2].start].strip():
            if _only_noun_number(_analyze(voikko, words[i + 2].text, cache)):
                continue
        out.append(Suggestion(
            rule='ATTR_AGREEMENT', category='grammar', severity='warning',
            start=offset + adj.start, end=offset + noun.end,
            message=('Kongruenssi: laatusana "%s" ja substantiivi "%s" ovat eri luvussa '
                     '(esim. "isot talot", "iso talo").' % (adj.text, noun.text)),
            replacements=[]))
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


# Aktiivin perfekti vaatii NUT-partisiipin ("olen mennyt"); TU-partisiippi on
# passiivin perfektin osa ja sen apuverbi on yksikon 3. persoonassa ("on menty").
# VISK §1292: "Liittomuodossa passiivin tunnus sijoittuu partisiippimuotoon,
# ja apuverbi on yksikön 3. persoonassa."
# VISK §530: intransitiiviverbien passiivin partisiippimuodot toimivat yleensa
# vain liittomuotojen ja verbiliittojen osana ("Sohvalla on istuttu").
# Siksi tarkistetaan vain valittuja intransitiiviverbeja: transitiiviverbin
# TU-partisiippi voi olla kelvollinen predikatiivi ("olen kiusattu",
# "olemme tehty samasta puusta").
# verbin perusmuoto -> (NUT-yksikko, NUT-monikko)
_INTRANSITIVE_NUT = {
    'mennä': ('mennyt', 'menneet'), 'tulla': ('tullut', 'tulleet'),
    'käydä': ('käynyt', 'käyneet'), 'kävellä': ('kävellyt', 'kävelleet'),
    'juosta': ('juossut', 'juosseet'), 'istua': ('istunut', 'istuneet'),
    'seistä': ('seisonut', 'seisoneet'), 'nukkua': ('nukkunut', 'nukkuneet'),
    'asua': ('asunut', 'asuneet'), 'lähteä': ('lähtenyt', 'lähteneet'),
    'saapua': ('saapunut', 'saapuneet'), 'palata': ('palannut', 'palanneet'),
    'jäädä': ('jäänyt', 'jääneet'), 'nousta': ('noussut', 'nousseet'),
    'uida': ('uinut', 'uineet'), 'matkustaa': ('matkustanut', 'matkustaneet'),
    'tanssia': ('tanssinut', 'tanssineet'), 'nauraa': ('nauranut', 'nauraneet'),
    'itkeä': ('itkenyt', 'itkeneet'), 'kulkea': ('kulkenut', 'kulkeneet'),
    'pysähtyä': ('pysähtynyt', 'pysähtyneet'),
    'ratsastaa': ('ratsastanut', 'ratsastaneet'),
    'hypätä': ('hypännyt', 'hypänneet'),
    'kiivetä': ('kiivennyt', 'kiivenneet'),
    'pudota': ('pudonnut', 'pudonneet'),
    'kaatua': ('kaatunut', 'kaatuneet'),
    'syntyä': ('syntynyt', 'syntyneet'),
    'kuolla': ('kuollut', 'kuolleet'),
    'herätä': ('herännyt', 'heränneet'),
    'väsyä': ('väsynyt', 'väsyneet'),
    'sairastua': ('sairastunut', 'sairastuneet'),
    'ehtiä': ('ehtinyt', 'ehtineet'),
    'viipyä': ('viipynyt', 'viipyneet'),
}
_OLLA_FINITE_NON3 = {
    'olen': 'singular', 'olet': 'singular', 'olemme': 'plural',
    'olette': 'plural', 'ovat': 'plural',
    'olin': 'singular', 'olit': 'singular', 'olimme': 'plural',
    'olitte': 'plural', 'olivat': 'plural',
}
_NEG_FOR_OLE = {'en', 'et', 'emme', 'ette', 'eivät'}
_PERFECT_ADVERBS = {'jo', 'vasta', 'juuri', 'aina', 'myös', 'vielä',
                    'sitten', 'koskaan', 'kyllä'}


_TU_CLITICS = ('kaan', 'kään', 'kin', 'han', 'hän', 'ko', 'kö', 'pa', 'pä')


def _split_tu_clitic(word):
    """Jaa TU/TY-loppuinen sana ja mahdollinen liitepartikkeli.

    Palauttaa (runko, liite): ("mentykin",) -> ("menty", "kin"). Palauttaa
    ('', '') jos sana ei ole TU/TY-loppuinen edes liitteen irrottamisen
    jalkeen. Liite '-s' jätetään tarkoituksella tunnistamatta (liian
    monimerkityksinen).
    """
    if word.endswith(('tu', 'ty')):
        return word, ''
    for suf in _TU_CLITICS:
        if word.endswith(suf) and word[:-len(suf)].endswith(('tu', 'ty')):
            return word[:-len(suf)], word[len(word) - len(suf):]
    return '', ''


def _passive_only_participle_verb(analyses):
    """Palauta verbin perusmuoto, jos sana on vain passiivin TU-partisiippi."""
    verbs = set()
    for a in analyses:
        if a.get('CLASS') != 'laatusana' or a.get('PARTICIPLE') != 'past_passive':
            return None
        fst = a.get('FSTOUTPUT') or ''
        m = re.search(r'\[Xp\]([^\[]+)\[X\]', fst)
        if not m:
            return None
        verbs.add(m.group(1))
    # sana, jolla on myos aktiivitulkinta (mennyt), ei ole vain passiivia
    return verbs.pop() if len(verbs) == 1 else None


def check_active_perfect_passive_participle(sent_text, offset, words, voikko, cache):
    """"Minä olen menty": persoonamuotoinen olla + passiivin TU-partisiippi.

    Passiivin perfekti on aina "on menty" (VISK §1292), joten olen/olet/
    olemme/olette/ovat (ja imperfektin vastineet) + intransitiiviverbin
    passiivipartisiippi on aktiivin perfektin virhe: "olen mennyt".
    Yksikon 3. persoona ("on menty", "kotiin on menty") ei osu.
    """
    out = []
    for i, tok in enumerate(words):
        low = tok.lower
        number = _OLLA_FINITE_NON3.get(low)
        if number is None and low == 'ole' and i > 0 \
                and words[i - 1].lower in _NEG_FOR_OLE:
            number = ('plural' if words[i - 1].lower in ('emme', 'ette', 'eivät')
                      else 'singular')
        if number is None:
            continue
        j = i + 1
        if j < len(words) and words[j].lower in _PERFECT_ADVERBS:
            j += 1
        if j >= len(words):
            continue
        nxt = words[j]
        if sent_text[words[j - 1].end:nxt.start].strip():
            continue  # valimerkki valissa
        # Suorituskyky: Passiivin menneen ajan TU-partisiipit päättyvät aina
        # päätteeseen 'tu' tai 'ty' (vokaalisointu), mahdollinen liitepartikkeli
        # ("mentykin") irrotetaan ensin. Vältetään kallis C-FFI:n morfologinen
        # analyysi (_analyze) sanoille, jotka eivät voi olla TU-partisiippeja.
        base, clitic = _split_tu_clitic(nxt.lower)
        if not base:
            continue
        forms = _INTRANSITIVE_NUT
        analyses = _analyze(voikko, nxt.text, cache)
        verb = _passive_only_participle_verb(analyses)
        if verb not in forms:
            continue
        sg, pl = forms[verb]
        # Muut liitteet säilytetään korjauksessa: "olen mentykin" ->
        # "olen mennytkin". Kysymysliite -ko/-kö kuuluu apuverbiin
        # ("Olenko mennyt?"), joten yhden sanan korjausta ei tarjota.
        base_repl = pl if number == 'plural' else sg
        question = clitic in ('ko', 'kö')
        repl = base_repl if question else base_repl + clitic
        if question:
            # Liite koko apuverbiokonaisuuteen: kielteisessä perfektissä
            # kieltoverbiin ("enkö ole mennyt"), myönteisessä olla-verbiin.
            # Olla-muodoissa on aina takavokaali, joten liite on -ko.
            if tok.lower == 'ole' and i > 0 and words[i - 1].lower in _NEG_FOR_OLE:
                example = f'{words[i - 1].text}kö ole {base_repl}'
            else:
                example = f'{tok.text}ko {base_repl}'
            hint = f' Kysymysliite siirretään apuverbiin: "{example}".'
        else:
            hint = ''

        out.append(Suggestion(
            rule='PERFECT_PASSIVE_PARTICIPLE', category='grammar',
            severity='error', start=offset + nxt.start, end=offset + nxt.end,
            message=('Aktiivin perfekti muodostetaan NUT-partisiipilla '
                     f'("{tok.text} {repl}"). TU-partisiippi kuuluu passiivin '
                     f'perfektiin, jossa apuverbi on yksikön 3. persoonassa '
                     f'("on {nxt.text}").' + hint),
            replacements=[] if question else [repl]))
    return out


# Typografia (Kielitoimiston ohjepankki). Kapeat, mekaaniset saannot:
#  - numero + %, € $ £ : valilyonti numeron ja merkin valiin
#    (https://kielitoimistonohjepankki.fi/ohje/prosenttimerkki/ ja .../rahasummat/)
#  - kellonaika pisteella, ei kaksoispisteella; ei etunollaa tunneissa
#    (https://kielitoimistonohjepankki.fi/ohje/ajanilmaukset-kellonajat-merkinta-ja-taivutus/)
#  - pisteelliset lyhenteet esim., jne., tms., yms., huom.
#    (https://kielitoimistonohjepankki.fi/ohje/lyhenteet-pisteelliset/)
_RE_PERCENT = re.compile(r'(?<![\w.,/%-])(\d+(?:,\d+)?)(%)(?!\w)')
_RE_CURRENCY = re.compile(r'(?<![\w.,/-])(\d+(?:,\d+)?)([€$£])(?![\w])')
_RE_CLOCK_COLON = re.compile(r'\b(klo|kello) (\d{1,2}):(\d{2})(?![\d:])', re.I)
_RE_CLOCK_ZERO = re.compile(r'\b(klo|kello) (0\d)(?:\.(\d{2}))?(?![\d:,]|\.\d)', re.I)
_DEC_UNITS = (r'(?:[\u00a0 ]?%|[\u00a0 ]?°C|[\u00a0 ](?:kg|g|km|m|cm|mm|l|dl|cl|€|'
              r'euroa|prosenttia|prosenttiyksikköä|metriä|kilometriä|kiloa|grammaa|'
              r'litraa|senttiä|astetta|vuotta|kuukautta|tuntia))')
_RE_DEC_POINT = re.compile(
    r'(?<![\w.,/:\-])(\d{1,3})\.(\d{1,2})(?=' + _DEC_UNITS + r'(?![\w]))', re.I)
_RE_ABBR = re.compile(r'(?<![\w.-])(esim|jne|tms|yms|huom)(?![\w.:-])', re.I)
# Numeroiden ryhmittely kolmen ryhmiin lopusta alkaen (ohjepankki,
# "Luvut ja numerot: numeroiden ryhmittely", luettu 2026-11-22):
# "5 603 075". Vahintaan 5-numeroinen kokonaisluku liputetaan sellaisenaan;
# 4-numeroinen vain yksikon edessa (vuosiluvut jäävät rauhaan).
# Ohitetaan: etunollalliset (puhelinnumerot "0401234567"), 10+ numeroiset
# (tilinumerot ja muut tunnukset), tunnus- ja laskentakontekstit
# (edessa # = + - * / ( ^ tai piste/kaksoispiste/viiva).
_RE_NUMGROUP5 = re.compile(r'(?<![\w.,:;/\-=+*\^(#])([1-9]\d{4,8})(?!\d)(?![.,:;/\-]\d)')
_RE_NUMGROUP4 = re.compile(
    r'(?<![\w.,:;/\-=+*\^(#])([1-9]\d{3})(?=' + _DEC_UNITS + r'(?![\w]))')
_RE_SS_VV = re.compile(r'(?<![\w.])(ss|vv)(\.)(?![\w])')
_DIGIT_CHARS = frozenset('0123456789')


def _group_digits(num):
    """Ryhmittele numeromerkkijono kolmen ryhmiin lopusta sitovalla valilla."""
    parts = []
    while len(num) > 3:
        parts.append(num[-3:])
        num = num[:-3]
    parts.append(num)
    return '\u00a0'.join(reversed(parts))
# Ajatusviiva lukujen rajakohdissa ja osapuolten tuloksissa (ohjepankki):
# 20-30 -> 20-30 (ajatusviiva), 2-1 -> 2-1. Ohitetaan tunnisteet (A380-800,
# UTF-8), viivaketjut (ISBN 978-951-..., ISO-paivays 2026-11-08) ja molemmin-
# puolin vahintaan 3-numeroiset mallinumerot (Boeing 737-800), ellei jompikumpi
# ole 1-2-numeroinen tai vuosisadaluku 1800-2199.
_RE_QUOTE_ASCII = re.compile(r'(?<!\d)"(?!\d)')
_RE_RANGE_HYPHEN = re.compile(r'(?<![\w\u2013.%-])(\d{1,4})-(\d{1,4})(?!-\d|[\w\u2013])')


def _is_yearish(s):
    return len(s) == 4 and 1800 <= int(s) <= 2199


def _range_hyphen_ok(a, b):
    # vuodet 1800-2199 kelpaavat aina, paitsi vuosi-kuukausi ("2026-11");
    # pienet (<=2-numeroiset) luvut ovat rajakohtia tai tuloksia ("16-20",
    # "2-1"); 3+3-numeroiset yhdistelmat ("737-800") ja "56-3"-mallit ovat
    # tunnisteita, ei rajakohtia
    if _is_yearish(a) or _is_yearish(b):
        return not (len(a) == 4 and len(b) == 2 and 1 <= int(b) <= 12)
    if len(a) <= 2 and len(b) <= 2:
        return not (len(b) == 1 and len(a) >= 2)
    return False



_RE_DATE_ISO = re.compile(
    r'(?<![\w/.-])(\d{4})-(\d{2})-(\d{2})(?![\w/-]|[ T]\d{2}[:.]\d{2})')
_RE_DATE_SLASH = re.compile(
    r'(?<![\w/.])(\d{1,2})/(\d{1,2})/(\d{4})(?![\w/])')


def _check_dates(sent_text, offset):
    """Paivaysmuodot (ohjepankki "Ajanilmaukset: paivays ja vuosiluku"):
    suomessa nouseva paivays pistein (24.12.2025). ISO 2025-12-24 on
    standardinmukainen mutta ei suositeltu suomenkielisessa tekstissa;
    kauttaviivat 24/12/2025 ovat vieras kaytanto."""
    out = []
    for m in _RE_DATE_ISO.finditer(sent_text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= mo <= 12 and 1 <= d <= 31):
            continue
        fixed = '%d.%d.%d' % (d, mo, y)
        out.append(Suggestion(
            rule='TYPO_DATE_FORMAT', category='style', severity='warning',
            start=offset + m.start(), end=offset + m.end(),
            message=('Suomenkielisessä tekstissä päiväys merkitään nousevasti '
                     'pistein ("%s"). Laskeva ISO-muoto on standardinmukainen '
                     'mutta ei suositeltu.' % fixed),
            replacements=[fixed]))
    for m in _RE_DATE_SLASH.finditer(sent_text):
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a > 31 or b > 31 or a == 0 or b == 0:
            continue
        repl = []
        if a > 12 and b <= 12:
            repl = ['%d.%d.%d' % (a, b, y)]
        elif b > 12 and a <= 12:
            repl = ['%d.%d.%d' % (b, a, y)]
        # molemmat <= 12: jarjestysta ei voi paatella, ei korjausta
        out.append(Suggestion(
            rule='TYPO_DATE_FORMAT', category='style', severity='warning',
            start=offset + m.start(), end=offset + m.end(),
            message='Suomenkielisessä tekstissä päiväys merkitään pistein, ei kauttaviivoin ("3.4.2025").',
            replacements=repl))
    return out


def _check_clock(sent_text, offset):
    out = []
    for m in _RE_CLOCK_COLON.finditer(sent_text):
        hh, mm = int(m.group(2)), int(m.group(3))
        if hh > 24 or mm > 59:
            continue
        out.append(Suggestion(
            rule='TYPO_CLOCK_FORMAT', category='style', severity='style',
            start=offset + m.start(), end=offset + m.end(),
            message=('Suomenkielisessä asiatekstissä tunnit ja minuutit erotetaan '
                     'pisteellä ("%s %d.%s"). Ohje on suositus.' % (m.group(1), hh, m.group(3))),
            replacements=['%s %d.%s' % (m.group(1), hh, m.group(3))]))
    for m in _RE_CLOCK_ZERO.finditer(sent_text):
        hh = int(m.group(2))
        if hh > 9:
            continue
        out.append(Suggestion(
            rule='TYPO_CLOCK_FORMAT', category='style', severity='style',
            start=offset + m.start(), end=offset + m.end(),
            message='Kellonaikaan ei yleensä merkitä etunollaa ("klo 9.15"). Ohje on suositus.',
            replacements=[]))
    return out


def _check_numgroup(sent_text, offset):
    """Numeroiden ryhmittely koko tekstille (libvoikko katkaisee virkkeen
    kaksoispisteeseen, joten osuu-suhde "30:12345" nakyisi palasina)."""
    out = []
    if _DIGIT_CHARS.isdisjoint(sent_text):
        return out
    for m in _RE_NUMGROUP5.finditer(sent_text):
        num = m.group(1)
        if re.match(r'\s*-[a-zåäö]', sent_text[m.end():]):
            continue  # yhdyssanan jatke ("80387-matematiikkasuorittimen")
        prev = sent_text[max(0, m.start() - 24):m.start()].rstrip()
        prev_word = prev.rsplit(' ', 1)[-1] if prev else ''
        if len(prev_word) >= 2 and prev_word.isalpha() and prev_word.isupper():
            continue  # standardi/tunnus ("ISO 26262", "IEC 61508")
        if len(num) == 5:
            rest = sent_text[m.end():].lstrip(' \u00a0')
            if rest[:1].isupper():
                continue  # postinumero ("33100 Tampere")
        fixed = _group_digits(num)
        out.append(Suggestion(
            rule='TYPO_NUMBER_GROUP', category='style', severity='warning',
            start=offset + m.start(1), end=offset + m.end(1),
            message=('Luku ryhmitellään kolmen numeron ryhmiin lopusta '
                     'alkaen ("%s").' % fixed),
            replacements=[fixed]))
    for m in _RE_NUMGROUP4.finditer(sent_text):
        num = m.group(1)
        fixed = _group_digits(num)
        out.append(Suggestion(
            rule='TYPO_NUMBER_GROUP', category='style', severity='warning',
            start=offset + m.start(1), end=offset + m.end(1),
            message=('Luku ryhmitellään kolmen numeron ryhmiin lopusta '
                     'alkaen ("%s").' % fixed),
            replacements=[fixed]))
    return out


def check_typography(sent_text, offset, clock=False):
    """clock=True: vain kellonaikasäännöt (ajetaan koko tekstille, koska
    libvoikko katkaisee virkkeen kaksoispisteeseen: 'klo 9:' + '15')."""
    out = []
    if clock:
        # koko teksti: libvoikko katkaisee virkkeen kaksoispisteeseen
        # ("klo 9:" + "15", "2025-04-03 12:" + "30")
        return (_check_clock(sent_text, offset) + _check_dates(sent_text, offset)
                + _check_numgroup(sent_text, offset))
    # Suorituskyky: Nopeat merkkisisältötarkistukset ('in') ennen regex-hakuja.
    # Valtaosassa luonnollisen kielen virkkeitä ei esiinny prosenttimerkkejä,
    # valuuttasymboleita, desimaalipisteitä tai yhdysmerkkejä.
    if '%' in sent_text:
        for m in _RE_PERCENT.finditer(sent_text):
            out.append(Suggestion(
                rule='TYPO_PERCENT_SPACE', category='style', severity='warning',
                start=offset + m.start(), end=offset + m.end(),
                message='Numeron ja prosenttimerkin väliin tulee välilyönti ("10 %").',
                replacements=[m.group(1) + '\u00a0%']))
    if '€' in sent_text or '$' in sent_text or '£' in sent_text:
        for m in _RE_CURRENCY.finditer(sent_text):
            out.append(Suggestion(
                rule='TYPO_CURRENCY_SPACE', category='style', severity='warning',
                start=offset + m.start(), end=offset + m.end(),
                message='Numeron ja rahayksikön tunnuksen väliin tulee välilyönti ("29,90 €").',
                replacements=[m.group(1) + '\u00a0' + m.group(2)]))
    if '.' in sent_text:
        for m in _RE_DEC_POINT.finditer(sent_text):
            fixed = '%s,%s' % (m.group(1), m.group(2))
            out.append(Suggestion(
                rule='TYPO_DECIMAL_POINT', category='style', severity='warning',
                start=offset + m.start(), end=offset + m.end(),
                message=('Suomenkielisessä tekstissä desimaaliluvun erottimena on '
                         'pilkku ("%s"), ei piste.' % fixed),
                replacements=[fixed]))
    if '"' in sent_text:
        # Suomenkielisessa tekstissa kaytetaan kaarevia lainausmerkkeja
        # (ohjepankki, "Lainausmerkit", luettu 2026-11-25). Ohitetaan
        # tuumamerkki (numeron vieressa).
        for m in _RE_QUOTE_ASCII.finditer(sent_text):
            out.append(Suggestion(
                rule='TYPO_QUOTE_MARK', category='style', severity='warning',
                start=offset + m.start(), end=offset + m.end(),
                message=('Suomenkielisessä tekstissä käytetään kaarevia '
                         'lainausmerkkejä (””), ei suoria lainausmerkkejä (").'),
                replacements=['\u201d']))
    if '-' in sent_text:
        for m in _RE_RANGE_HYPHEN.finditer(sent_text):
            if not _range_hyphen_ok(m.group(1), m.group(2)):
                continue
            prev = sent_text[max(0, m.start() - 12):m.start()].rstrip().rsplit(' ', 1)[-1].rstrip(':').lower()
            if len(m.group(1)) == 4 and len(m.group(2)) == 4 and \
                    (m.group(1).startswith('0') or m.group(2).startswith('0') or
                     prev.split('-')[0] in ('issn', 'isbn', 'ismn', 'doi', 'sku', 'id') or
                     re.search(r'-(numero|tunnus|nro|koodi)$', prev)):
                continue  # tunnuksenmuotoinen 4+4-pari ("ISSN-koodi 0355-2047",
                # "SKU-numero 2020-1230"); tavallinen pieni vali
                # ("ISBN-numeron 5-8 merkkiä") liputetaan
            before = sent_text[:m.start()].rstrip()
            after = sent_text[m.end():].lstrip()
            if after.startswith('='):
                rhs = after[1:].lstrip()
                tok = rhs.split()[0].rstrip('.,;:!?)]') if rhs else ''
                if tok and (tok[0].isdigit() or tok[0] in '+-(' or
                            re.fullmatch(r'[A-Za-z\u00c5\u00c4\u00d6\u00e5\u00e4\u00f6]\d*'
                                         r'(?:[+\-*/^][A-Za-z\u00c5\u00c4\u00d6\u00e5\u00e4\u00f6]?\d*)*'
                                         r'[\u00b2\u00b3\u00b9\u2070\u2074-\u2079]?', tok)):
                    continue  # yhtalo ("2-1=1", "2-1=x"), ei rajakohta;
                    # "= kotijoukkueen voitto" on selitys, liputetaan
            if before and before[-1] in '=+-*/':
                operand = before[:-1].rstrip()
                if operand and (operand[-1].isdigit() or operand[-1] in '+-*/('):
                    continue  # laskutoimituksen osa ("1=2-1", "5=3+2-1");
                    # sanan perassa oleva "=" on arvon antoa ("Ika=20-30 vuotta")
            if before.endswith('('):
                lead = sent_text[:m.start()].rstrip()[:-1]
                prev_ch = lead[-1] if lead else ''
                if prev_ch.isdigit() or prev_ch in '+-*/(':
                    continue  # aritmetiikan sulku ("1+(2-1)");
                    # "Ryhmä 1 (10-12-vuotiaat)" on otsikkotaso, liputetaan
            fixed = '%s\u2013%s' % (m.group(1), m.group(2))
            out.append(Suggestion(
                rule='TYPO_RANGE_HYPHEN', category='style', severity='warning',
                start=offset + m.start(), end=offset + m.end(),
                message=('Lukujen rajakohtien ja osapuolten tulosten v\u00e4liss\u00e4 '
                         'k\u00e4ytet\u00e4\u00e4n ajatusviivaa ("%s"), ei yhdysmerkki\u00e4.' % fixed),
                replacements=[fixed]))
    for m in _RE_ABBR.finditer(sent_text):
        word = m.group(1)
        out.append(Suggestion(
            rule='TYPO_ABBR_DOT', category='spelling', severity='warning',
            start=offset + m.start(), end=offset + m.end(),
            message='Lyhenteen perässä on piste ("%s.").' % word.lower(),
            replacements=[word + '.']))
    if 'ss.' in sent_text or 'vv.' in sent_text:
        for m in _RE_SS_VV.finditer(sent_text):
            old = m.group(1) + '.'
            fixed = m.group(1)[0] + '.'
            out.append(Suggestion(
                rule='ABBR_SS_VV', category='style', severity='style',
                start=offset + m.start(), end=offset + m.end(),
                message=('Lyhenne "%s" on vanhentunut; nykyisin käytetään '
                         'lyhennettä "%s".' % (old, fixed)),
                replacements=[fixed]))
    return out


# Pilkku alistuskonjunktion edella: alistuskonjunktiolla alkava sivulause
# erotetaan paalauseesta pilkulla (ohjepankki, "Pilkku ja
# alistuskonjunktiolla (esim. etta, jos) alkava lause", luettu 2026-11-25).
# Ohjepankin poikkeukset: yhden sanan paalause + hyvin lyhyt sivulause ->
# pilkku valinnainen ("Toivon etta tulet."); perakkaiset konjunktiot
# ("tai jos", "mutta vaikka", "etta kun") ilman pilkkua; korostussanan
# kanssa ("etenkin jos") pilkku voi olla korostussanan kummallakin puolella.

_SUBORD_CONJ = {
    'että', 'jotta', 'koska', 'kun', 'kunnes', 'jos', 'vaikka',
    'jollei', 'ellei', 'kunhan', 'mikäli', 'joskin',
}

# Sanat, joiden jalkeen konjunktiota edeltava pilkku joko ei kuulu
# (konjunktioparit) tai voi sijaita aiemmin lauseessa (korostussanat),
# tai yhdistelma on idiomaattinen ("mita jos").
_SUBORD_PREV_SKIP = {
    'mutta', 'vaan', 'ja', 'tai', 'vai', 'sekä', 'eli', 'kuin',
    'että', 'jos', 'kun', 'vaikka', 'koska', 'jotta', 'kunnes',
    'jollei', 'ellei', 'kunhan', 'mikäli', 'joskin',
    'etenkin', 'varsinkin', 'erityisesti', 'erityisen', 'nimenomaan',
    'juuri', 'vasta', 'heti', 'myös', 'paitsi', 'mitä', 'entä',
}

# "vaikka" + naa: samantekevyytta tai puhekielta ("vaikka mita")
_VAIKKA_NEXT_SKIP = {'mitä', 'mikä', 'kuinka', 'miten', 'vaan', 'vielä'}


def check_comma_subordinate(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        if tok.lower not in _SUBORD_CONJ or i < 2:
            # i == 0: virkkeen alku; i == 1: yhden sanan paalause,
            # jolloin pilkku on ohjepankin mukaan valinnainen
            continue
        if tok.text[:1].isupper():
            # kesken virkkeen isolla alkava: erisnimi tai otsikon jalkeinen
            # virkkeen alku (piste puuttuu) - ei konjunktiotarkistusta
            continue
        prev = words[i - 1]
        if sent_text[prev.end:tok.start].strip() != '':
            # pilkku on jo paikallaan tai valissa on raja-merkki
            # (":", "-", sulku tai lainausmerkki)
            continue
        if prev.lower in _SUBORD_PREV_SKIP:
            continue
        if tok.lower == 'että' and any(
                w.lower == 'sekä' for w in words[max(0, i - 6):i]):
            continue  # korrelaatti "sekä asiakkaiden että työntekijöiden"
        if (tok.lower == 'vaikka' and i + 1 < len(words)
                and words[i + 1].lower in _VAIKKA_NEXT_SKIP):
            continue
        out.append(Suggestion(
            rule='PUNCT_COMMA_SUBORD', category='style', severity='warning',
            start=offset + tok.start, end=offset + tok.end,
            message=('Alistuskonjunktiolla "%s" alkava sivulause erotetaan '
                     'päälauseesta pilkulla (", %s").' % (tok.text, tok.text)),
            replacements=[', ' + tok.text]))
    return out


# Relatiivilause erotetaan paalauseesta pilkulla (ohjepankki, "Pilkku ja
# joka-, mika-relatiivilause", luettu 2026-11-25). Ohje ei tunne
# lyhyyspoikkeusta, joten pilkku vaaditaan aina kesken virkkeen.
# Relatiivipronominit joka ja mika taivutusmuotoineen; jolloin/joten/
# milloin/miten-tyyppiset jatetaan tarkoituksella pois (kysymys- ja
# konnektorimerkitykset).

_REL_PLAIN = {
    'jonka', 'jota', 'jolle', 'jolta', 'jolla', 'josta', 'johon', 'jossa',
    'jonne', 'jotka', 'joiden', 'joita', 'joille', 'joilta', 'joilla',
    'joista', 'joihin', 'joissa', 'joina', 'joiksi',
    'minkä', 'mitä', 'mille', 'miltä', 'millä', 'mistä', 'mihin', 'missä',
    'minne', 'mitkä',
}

# joka/mika ovat myos maaraissanoja ("joka paiva", "mika paiva"):
# liputetaan vain, kun seuraava sana ei ole nomini.
_REL_QUANT = {'joka', 'mikä'}

# konjunktiopari tai idioomi ("kerro, mita teit ja mita nait"; "mita jos")
_REL_PREV_SKIP = {
    'ja', 'tai', 'vai', 'että', 'mutta', 'vaan', 'sekä', 'eli',
    'mitä', 'entä', 'mikä', 'joka',
}

_REL_NOMINAL_CLASSES = {'nimisana', 'laatusana', 'lukusana'}


def _rel_next_is_nominal(voikko, cache, word):
    for a in _analyze(voikko, word, cache):
        if a.get('CLASS') in _REL_NOMINAL_CLASSES and not a.get('PARTICIPLE'):
            return True
    return False


def _rel_next_is_superlative(voikko, cache, word):
    return any(a.get('COMPARISON') == 'superlative'
               for a in _analyze(voikko, word, cache))


def check_comma_relative(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        low = tok.lower
        if low not in _REL_PLAIN and low not in _REL_QUANT:
            continue
        if i == 0:
            continue  # virkkeen alku
        if tok.text[:1].isupper():
            continue  # erisnimi (esim. Jolla) tai otsikon jalkeen
        prev = words[i - 1]
        if sent_text[prev.end:tok.start].strip() != '':
            continue  # pilkku tai raja-merkki jo valissa
        if prev.lower in _REL_PREV_SKIP:
            continue
        if i + 1 < len(words) and words[i + 1].lower in (
                'tahansa', 'hyvänsä', 'vain'):
            continue  # "mikä tahansa", "mitä vain": yleispronomini
        if low == 'mitä' and i + 1 < len(words) and \
                _rel_next_is_superlative(voikko, cache, words[i + 1].text):
            continue  # "mitä hienoin lahja": superlatiivin vahvike
        if low in _REL_QUANT and i + 1 < len(words) and \
                _rel_next_is_nominal(voikko, cache, words[i + 1].text):
            continue  # "joka paiva", "mika vuosi": maaraissana
        out.append(Suggestion(
            rule='PUNCT_COMMA_RELATIVE', category='style', severity='warning',
            start=offset + tok.start, end=offset + tok.end,
            message=('Relatiivipronominilla "%s" alkava relatiivilause '
                     'erotetaan päälauseesta pilkulla (", %s").'
                     % (tok.text, tok.text)),
            replacements=[', ' + tok.text]))
    return out


# Pilkku kokonaisten paalauseiden valissa, kun niita yhdistaa
# rinnastuskonjunktio (ohjepankki, "Pilkku paalauseiden valissa", luettu
# 2026-11-25). Pilkku vaaditaan, kun molemmat lauseet ovat rakenteeltaan
# kokonaisia (omalla subjektilla). Valinnainen eli EI liputeta: 1./2.
# persoonan verbit, passiiviverbit, hyvin lyhyet lauseet, yhteinen jasen.
# mutta/vaan on oma saantonsa (PUNCT_COMMA_MUTTA_VAAN); tassa ja, tai,
# silla.

_RINN_CONJ = {'ja', 'tai', 'sillä'}

_RINN_PREV_SKIP = {
    'ja', 'tai', 'vai', 'sekä', 'eli', 'mutta', 'vaan', 'sillä', 'kuin',
    'että', 'jos', 'kun', 'vaikka', 'koska', 'jotta', 'kunnes',
    'jollei', 'ellei', 'kunhan', 'mikäli', 'joskin',
}

_RINN_KIELTO_3RD = {'ei', 'eivät', 'eikö', 'eivätkö'}


def _finite_active_3rd_verb(analyses):
    return any(a.get('CLASS') == 'teonsana' and a.get('PERSON') == '3'
               and a.get('MOOD') in ('indicative', 'conditional', 'potential')
               and not a.get('PARTICIPLE') and not a.get('INFINITIVE')
               and a.get('NEGATIVE') not in ('true', True)
               and a.get('VOICE') != 'passive'
               for a in analyses)


def check_comma_rinnastus(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        if tok.lower not in _RINN_CONJ or i == 0:
            continue
        if tok.text[:1].isupper():
            continue  # erisnimi tai otsikon jalkeinen virkkeen alku
        prev = words[i - 1]
        if sent_text[prev.end:tok.start].strip() != '':
            continue  # pilkku tai raja-merkki jo valissa
        if prev.lower in _RINN_PREV_SKIP:
            continue
        if tok.lower in ('ja', 'tai'):
            if i < 3:
                # hyvin lyhyet paalauseet (2-3 sanaa): pilkku valinnainen
                continue
            if prev.text.endswith('-'):
                continue  # ripustettu yhdyssanan osa ("Etela- ja lounais-")
            if not _analyze(voikko, prev.text, cache):
                continue  # tuntematonta sanaa ei voi paatella (vieras/lyhenne)
            if i + 2 >= len(words):
                continue
            nxt = words[i + 1]
            if not _nom_subject(_analyze(voikko, nxt.text, cache)):
                continue
            verb = words[i + 2]
            verb_an = _analyze(voikko, verb.text, cache)
            plural = verb.lower in ('eivät', 'eivätkö') or any(
                a.get('NUMBER') == 'plural' for a in verb_an)
            if plural and _nom_subject(_analyze(voikko, prev.text, cache)):
                # "maanviljely ja karjanhoito yleistyivat": kahden
                # nominatiivin muodostama luettelosubjekti, ei pilkkua
                continue
            if _neg_base(verb.lower) in _KIELTO:
                # 1./2. persoonan kieltoverbi -> pilkku valinnainen
                if verb.lower not in _RINN_KIELTO_3RD:
                    continue
            elif not _finite_active_3rd_verb(verb_an):
                # passiivi ja 1./2. persoona: pilkku valinnainen -> ohitus
                continue
        else:  # silla
            if i + 1 >= len(words):
                continue
            nxt = words[i + 1]
            if _neg_base(nxt.lower) in _KIELTO:
                if nxt.lower not in _RINN_KIELTO_3RD:
                    continue
            elif not _finite_active_3rd_verb(_analyze(voikko, nxt.text, cache)):
                continue  # "silla kynalla": adessiivipronomini, ei konjunktio
        out.append(Suggestion(
            rule='PUNCT_COMMA_RINNASTUS', category='style', severity='warning',
            start=offset + tok.start, end=offset + tok.end,
            message=('Kokonaisia päälauseita yhdistävän konjunktion "%s" '
                     'edellä on pilkku (", %s").' % (tok.text, tok.text)),
            replacements=[', ' + tok.text]))
    return out


# Vertailevan kuin-sanan edella ei kayteta pilkkua (ohjepankki, "Pilkku
# kuin-ilmauksissa", luettu 2026-11-25). Liputetaan liallinen pilkku suoraan
# kuin-sanan edella. Ohitetaan edeltavat ikään/ennen/toisin/samoin/aivan/
# niin, joiden kanssa pilkku on ohjeen mukaan valinnainen tauottava keino.

_KUIN_PREV_ALLOW_COMMA = {'ikään', 'ennen', 'toisin', 'samoin', 'aivan', 'niin'}


def _finite_verb_any(analyses):
    return any(a.get('CLASS') == 'teonsana' and a.get('MOOD') in (
        'indicative', 'conditional', 'potential') and not a.get('PARTICIPLE')
        and not a.get('INFINITIVE') for a in analyses)


def check_comma_kuin(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        if tok.lower != 'kuin' or i == 0:
            continue
        prev = words[i - 1]
        gap = sent_text[prev.end:tok.start]
        if gap.strip() != ',':
            continue  # vain suoraan edeltava pilkku
        if prev.lower in _KUIN_PREV_ALLOW_COMMA:
            continue
        if not any(a.get('COMPARISON') == 'comparative'
                   for a in _analyze(voikko, prev.text, cache)) and any(
                _finite_verb_any(_analyze(voikko, w.text, cache))
                for w in words[i + 1:i + 5]):
            continue  # irrallinen kuin-lause: pilkku sallittu (ohjepankki)
        out.append(Suggestion(
            rule='PUNCT_COMMA_KUIN', category='style', severity='warning',
            start=offset + prev.end, end=offset + tok.end,
            message=('Vertailevan kuin-sanan edellä ei käytetä pilkkua '
                     '("%s kuin").' % prev.text),
            replacements=[' kuin']))
    return out


# Lainauksen ja johtolauseen valiin tulee pilkku, kun valittainmuotoinen
# lainaus on johtolauseen edella: '"En aio erota", ministeri vastasi.'
# (ohjepankki, "Pilkku lainauksen ja johtolauseen jaljessa", luettu
# 2026-11-25). Kysymys-/huutomerkin jalkeen pilkkua ei tule; kolmen
# pisteen jalkeen pilkku on valinnainen.

_JOHTO_VERBS = {
    'sanoi', 'sanoo', 'kysyi', 'kysyy', 'vastasi', 'vastaa', 'totesi',
    'toteaa', 'kertoi', 'kertoo', 'huomautti', 'huomauttaa', 'lisäsi',
    'lisää', 'jatkoi', 'jatkaa', 'kommentoi', 'selitti', 'selittää',
    'väitti', 'väittää', 'ilmoitti', 'ilmoittaa', 'tiedotti', 'kirjoitti',
    'kirjoittaa', 'huudahti', 'lausahti', 'toisti', 'myönsi', 'myöntää',
    'väiteli', 'arveli', 'arvioi', 'paalutti', 'pahoitteli', 'kiitti',
}

_RE_JOHTO = re.compile(
    r'(.)[”"](\s+)(?:(\w+)\s+)?(%s)\b' % '|'.join(sorted(_JOHTO_VERBS)))


def check_comma_johtolause(sent_text, offset, words, voikko, cache):
    out = []
    for m in _RE_JOHTO.finditer(sent_text):
        if m.group(1) in '!?….':
            continue  # kysymys-/huutomerkin (tai ...) jalkeen ei pilkkua
        verb = m.group(4)
        opener = max(sent_text.rfind(q, 0, m.start() + 1) for q in '”"“')
        if opener > 0 and sent_text[:opener].strip():
            continue  # otsikko tms. lauseen keskellä ("Elokuva "X" kertoo")
        # span: lainausmerkki + vali + mahdollinen johtolauseen subjekti
        start = m.start() + 1
        end = m.start(4)
        quote = sent_text[m.start() + 1]
        tail = sent_text[start + 1:end]
        out.append(Suggestion(
            rule='PUNCT_COMMA_JOHTOLAUSE', category='style', severity='warning',
            start=offset + start, end=offset + end,
            message=('Väittämän muotoisen lainauksen ja johtolauseen väliin '
                     'tulee pilkku ("…", %s …).' % verb),
            replacements=[quote + ',' + tail]))
    return out


# Lauseenvastiketta (ja ilman-/tekemalla-rakennetta) ei eroteta muusta
# lauseesta pilkulla, olipa vastike virkkeen alussa tai lopussa
# (ohjepankki, "Pilkku ja lauseenvastike: auringon noustua lahdimme",
# luettu 2026-11-25). Poikkeus: vastikkeen jalkeen tuleva etta-sivulause
# erotetaan pilkulla ("uskoen, etta voin auttaa").

_LV_CONJ = {'että', 'jos', 'kun', 'ja', 'tai', 'mutta', 'vaan', 'sillä',
            'koska', 'vaikka', 'kuin', 'niin', 'eli', 'sekä', 'vai',
            'jotta', 'mikäli'}


def _lv_marker(voikko, cache, word):
    """E-/A-infinitiivi tai menneen toiminnan partisiippi omalla
    possessiivisuffiksilla, tai ma-infinitiivin adessiivi (tekemalla)."""
    for a in _analyze(voikko, word, cache):
        mood = a.get('MOOD')
        if mood in ('E-infinitive', 'A-infinitive') and a.get('POSSESSIVE'):
            return True
        if mood == 'MA-infinitive' and a.get('SIJAMUOTO') == 'ulkoolento' \
                and a.get('CLASS') == 'teonsana':
            return True
        if a.get('PARTICIPLE') == 'past_passive' and a.get('POSSESSIVE'):
            return True
    return False


def _lv_gen_pattern_marker(voikko, cache, word):
    """Omanto-subjektin vastikkeen loppusana: 'auringon noustua',
    'Suomen kesän ollessa' (ei vaadi possessiivia)."""
    for a in _analyze(voikko, word, cache):
        if a.get('CLASS') == 'teonsana' and a.get('MOOD') == 'E-infinitive':
            return True
        if a.get('PARTICIPLE') == 'past_passive' \
                and a.get('SIJAMUOTO') == 'osanto':
            return True
    return False


def _lv_first_finite(words, voikko, cache):
    # "vastata" saa myos passiivin indikatiivin analysin; ohita sanat,
    # joilla on infinitiivi- tai partisiippianalyysi (monitulkintaiset).
    for i, w in enumerate(words):
        an = _analyze(voikko, w.text, cache)
        if any(a.get('INFINITIVE') or a.get('MOOD', '').endswith('-infinitive')
               or a.get('PARTICIPLE') for a in an):
            continue
        if _finite_verb_any(an):
            return i
    return len(words)


def check_comma_lauseenvastike(sent_text, offset, words, voikko, cache):
    out = []

    def flag(i, why):
        # pilkku sanojen i ja i+1 valissa
        a, b = words[i], words[i + 1]
        if b.lower in _LV_CONJ:
            return  # konjunktiota seuraava lause erotetaan pilkulla
        gap = sent_text[a.end:b.start]
        if gap.strip() != ',':
            return
        if any(s.start == offset + a.end for s in out):
            return  # jo liputettu (R1 ja R3 voivat osua samaan)
        out.append(Suggestion(
            rule='PUNCT_COMMA_LAUSEENVASTIKE', category='style',
            severity='warning',
            start=offset + a.end, end=offset + b.start,
            message=('Lauseenvastiketta ei eroteta pilkulla (%s).'
                     % why),
            replacements=[' ']))

    # R1/R4: pilkku vastikkeen jalkeen. Vastike aloittaa virkkeen, kun
    # 1. sana on vastikemerkki, genetiivisubjekti tai "ilman".
    if len(words) >= 3:
        w0 = words[0]
        initial = _lv_marker(voikko, cache, w0.text)
        gen_pattern = False
        if not initial and w0.lower == 'ilman' and any(
                a.get('CLASS') == 'suhdesana'
                for a in _analyze(voikko, w0.text, cache)):
            initial = True  # ilman-rakenne ("Ilman oppeja, ei olisi...")
        if not initial and any(a.get('SIJAMUOTO') == 'omanto'
                               for a in _analyze(voikko, w0.text, cache)):
            # omanto-alku: etsi vastikkeen loppusana ennen pilkkua
            fin = _lv_first_finite(words, voikko, cache)
            for j in range(1, min(fin, len(words) - 1)):
                if _lv_gen_pattern_marker(voikko, cache, words[j].text):
                    gen_pattern = True
                    break
        if initial or gen_pattern:
            if initial and _lv_marker(voikko, cache, w0.text) is False \
                    and gen_pattern is False and w0.lower == 'ilman' and \
                    len(words) > 1 and words[1].lower == 'muuta':
                pass  # "Ilman muuta, ..." korostusilmaus
            else:
                fin = _lv_first_finite(words, voikko, cache)
                for i in range(min(fin, len(words) - 1)):
                    if sent_text[words[i].end:words[i + 1].start]\
                            .strip() == ',':
                        if w0.lower == 'ilman' and (
                                words[1].lower == 'että' or any(
                                    w.lower in ('ja', 'tai', 'sekä', 'eli', 'vai')
                                    for w in words[i + 1:fin])):
                            break  # "ilman että" tai luettelon pilkku
                        flag(i, '"%s ..."' % w0.text)
                        break

    # R2: pilkku suoraan ennen vastikemerkkia ("... saada, muuttaessaan")
    for i, tok in enumerate(words):
        if i == 0:
            continue
        prev = words[i - 1]
        if sent_text[prev.end:tok.start].strip() != ',':
            continue
        if _lv_marker(voikko, cache, tok.text):
            flag(i - 1, '"%s"-alkuinen vastike' % tok.text)
        elif tok.lower == 'ilman' and any(
                a.get('CLASS') == 'suhdesana'
                for a in _analyze(voikko, tok.text, cache)):
            if not (i + 1 < len(words) and words[i + 1].lower in ('muuta', 'että')) \
                    and ',' not in sent_text[:prev.end]:
                flag(i - 1, 'ilman-rakenne')

    # R3: pilkku suoraan vastikemerkin jalkeen ("Soitettuaan, hän...")
    for i, tok in enumerate(words):
        if i + 1 >= len(words):
            continue
        if not _lv_marker(voikko, cache, tok.text):
            continue
        if sent_text[tok.end:words[i + 1].start].strip() == ',':
            flag(i, '"%s"-paatteinen vastike' % tok.text)
    return out


# Luettelon osien valiin tulee pilkku, mutta viimeisen osan ja-/seka-/tai-
# sanan eteen pilkkua EI tule: "Kivea, Saarikoskea, Kilpea, Hassista ja
# muita" (ohjepankki, "Pilkku rinnasteisten lauseenjasenten ja luettelon
# osien valissa", luettu 2026-11-25). Liputetaan vain selvat nimiluettelot:
# ohitetaan, jos ja-sanan jalkeen on nominatiivi + aarellisverbi
# (kokonainen paa/sivulause, jolloin pilkku on pakollinen) tai jos
# edellisen pilkun ja ja-sanan valissa on aarellisverbi (lauseketju).

_LJA_CONJ = {'ja', 'sekä', 'tai'}


def check_comma_list_ja(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        if tok.lower not in _LJA_CONJ or i < 2:
            continue
        prev = words[i - 1]
        gap = sent_text[prev.end:tok.start]
        if gap.strip() != ',':
            continue
        # vaadi aiempi pilkku samassa lauseessa (>= 3 osan luettelo)
        j = i - 2
        while j >= 0 and sent_text[words[j].end:words[j + 1].start]\
                .strip() != ',':
            j -= 1
        if j < 0:
            continue  # vain kaksi osaa: konjunktiopari, ei liputeta
        # aarellisverbi edellisen pilkun ja konjunktion valissa -> lauseketju
        if any(_finite_verb_any(_analyze(voikko, w.text, cache))
               for w in words[j + 1:i]):
            continue
        # kuten-tarkennus edellisen pilkun ja konjunktion valissa ->
        # pilkku sulkee tarkennuksen, ei luettelon osaa
        if any(w.lower == 'kuten' for w in words[j + 1:i]):
            continue
        # konjunktion jalkeen aarellisverbi -> kokonainen lause
        # (esim. eksistentiaali "ja sillä oli oma hallinto")
        if any(_finite_verb_any(_analyze(voikko, w.text, cache))
               for w in words[i + 1:]):
            continue
        out.append(Suggestion(
            rule='PUNCT_COMMA_LIST_JA', category='style',
            severity='warning',
            start=offset + prev.end, end=offset + tok.start,
            message=('Luettelon viimeisen osan %s-sanan edella ei '
                     'kayteta pilkkua.' % tok.text),
            replacements=[' %s' % tok.text]))
    return out


# Epasuora (alisteinen) kysymyslause erotetaan paalauseesta pilkulla:
# "En tieda, missa han asuu." (ohjepankki, "Pilkku ja epasuora
# kysymyslause: Han kysyi, tulenko ajoissa.", luettu 2026-11-25).
# Tunnistetaan vain selkein tapaus: matriisiverbi (kysya, tietaa, ...)
# + suoraan perassa kysymyssana tai -ko/-ko-verbi ilman pilkkua.

_IQ_MATRIX = {
    'kysyä', 'tietää', 'arvata', 'veikata', 'ennustaa', 'kuulla',
    'miettiä', 'pohtia', 'ihmetellä', 'päätellä', 'selvittää', 'muistaa',
    'unohtaa', 'ymmärtää', 'kertoa', 'nähdä', 'huomata', 'arvella',
    'tuumia', 'määritellä', 'tutkia', 'selvitellä', 'arvioida', 'katsoa',
    'päättää', 'testata', 'arpoa', 'tarkistaa', 'tarkastella', 'harkita',
}

_IQ_QWORDS = {
    'kuka', 'ken', 'kenet', 'kenestä', 'kenellä', 'kenelle', 'kenen',
    'keneltä', 'keneen', 'keneksi', 'mikä', 'mitä', 'minkä', 'missä',
    'mistä', 'mihin', 'millä', 'mille', 'miltä', 'miksi', 'miten',
    'milloin', 'kuinka', 'kumpi', 'kumman', 'kummassa', 'kummasta',
    'kumpaan', 'kummalla', 'kummalle', 'kummalta', 'millainen',
    'millaista', 'minkälainen', 'monenko',
}


def _iq_is_matrix_verb(voikko, cache, word):
    return any(a.get('CLASS') == 'teonsana'
               and a.get('BASEFORM') in _IQ_MATRIX
               for a in _analyze(voikko, word, cache))


def _iq_is_ko_verb(voikko, cache, word):
    low = word.lower()
    return len(low) >= 4 and low.endswith(('ko', 'kö')) and any(
        a.get('CLASS') == 'teonsana' for a in _analyze(voikko, word, cache))


def check_comma_indirect_question(sent_text, offset, words, voikko, cache):
    out = []
    for i in range(1, len(words) - 1):
        q = words[i]
        if q.lower not in _IQ_QWORDS and not _iq_is_ko_verb(
                voikko, cache, q.text):
            continue
        prev = words[i - 1]
        gap = sent_text[prev.end:q.start]
        if gap.strip() != '':
            continue  # pilkku tai muu merkki jo valissa
        if i + 1 < len(words) and words[i + 1].lower in (
                'tahansa', 'hyvänsä', 'vain'):
            continue  # yleispronomini ("mitä vain"), ei kysymyslause
        if not _iq_is_matrix_verb(voikko, cache, prev.text):
            continue
        out.append(Suggestion(
            rule='PUNCT_COMMA_INDIRECT_QUESTION', category='style',
            severity='warning',
            start=offset + prev.end, end=offset + q.start,
            message=('Epäsuora kysymyslause erotetaan päälauseesta '
                     'pilkulla ("%s, %s").' % (prev.text, q.text)),
            replacements=[', ']))
    return out


# Nimea tasmentavien perusmuotoisten titteleiden valiin tulee pilkku:
# "toimitusjohtaja, ekonomi Liisa Jarvinen" (ohjepankki, "Pilkku
# titteleiden valissa: johtaja, insinoori Virta", luettu 2026-11-25).
# Kun ensimmaisella tittelilla on oma määrite ("laitoksen johtaja"),
# pilkku on valinnainen -> liputetaan vain kahden perusmuotoisen
# tittelin suora perakkaisyys ilman pilkkua.

_TITLES = {
    'toimitusjohtaja', 'johtaja', 'päällikkö', 'lehtori', 'rehtori',
    'professori', 'dosentti', 'dekaani', 'ekonomi', 'maisteri',
    'tohtori', 'lisensiaatti', 'insinööri', 'arkkitehti', 'opettaja',
    'neuvos', 'puheenjohtaja', 'sihteeri', 'kapteeni', 'valmentaja',
    'päätoimittaja', 'yliopettaja', 'apulaisprofessori', 'tutkija',
    'pääjohtaja', 'konsuli', 'ministeri', 'arkkienkeli', 'piispa',
    'rovasti', 'pastori', 'ylilääkäri', 'lääkäri', 'hammaslääkäri',
    'asessori', 'esimies', 'varatuomari', 'ft',
}


def check_comma_titles(sent_text, offset, words, voikko, cache):
    out = []
    for i in range(len(words) - 2):
        a, b, c = words[i], words[i + 1], words[i + 2]
        if a.lower not in _TITLES or b.lower not in _TITLES:
            continue
        if sent_text[a.end:b.start].strip() != '':
            continue  # pilkku tai muu merkki jo valissa
        # vaadi perusmuoto (nimento) molemmille: ohje koskee vain
        # määritteettomia perusmuotoja; FT-tyyppiset lyhenteet kelpaavat
        def base_form(w):
            return any(an.get('CLASS') in ('nimisana', 'lyhenne')
                       and an.get('SIJAMUOTO') in ('nimento', None)
                       for an in _analyze(voikko, w.text, cache))
        if not base_form(a) or not base_form(b):
            continue
        # edeltava omanto on ensimmaisen tittelin määrite
        # ("Laitoksen johtaja tohtori") -> pilkku valinnainen, ohitetaan
        if i > 0 and any(an.get('SIJAMUOTO') == 'omanto'
                         for an in _analyze(voikko, words[i - 1].text, cache)):
            continue
        # titteliparin jalkeen tulee nimi (iso alkukirjain)
        if not c.text[:1].isupper():
            continue
        if b.text[:1].isupper() and not b.text.isupper():
            continue  # isolla alkava toinen sana on sukunimi ("kapteeni Piispa")
        if i > 0 and any(an.get('CLASS') == 'nimisana_laatusana'
                         for an in _analyze(voikko, words[i - 1].text, cache)):
            continue  # "entinen ministeri professori": määrite, pilkku valinnainen
        out.append(Suggestion(
            rule='PUNCT_COMMA_TITLES', category='style', severity='warning',
            start=offset + a.end, end=offset + b.start,
            message=('Nimeä täsmentävien perusmuotoisten titteleiden '
                     'välissä on pilkku ("%s, %s").' % (a.text, b.text)),
            replacements=[', ']))
    return out


# Kuten-jakso, joka on kokonainen lause (sisaltaa persoonamuotoisen
# verbin), erotetaan paalauseesta pilkulla: "Sailiot ovat huonossa
# kunnossa, kuten kuvasta nakykin." Samoin 'esimerkiksi'-merkityksinen
# kuten-jakso erotetaan aina pilkulla (ohjepankki, "Konjunktiot: kuten",
# luettu 2026-11-25). 'Niin kuin' -merkityksinen sananjakso ilman verbia
# ("Lomaile kuten kuninkaalliset") ei saa pilkkua, joten liputetaan vain
# kun kuten-sanaa seuraavien sanojen joukossa on aarellisverbi.

def check_comma_kuten(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        if tok.lower != 'kuten' or i == 0:
            continue
        prev = words[i - 1]
        gap = sent_text[prev.end:tok.start]
        if gap.strip() != '':
            continue  # pilkku tai muu merkki jo valissa
        span = []
        for k in range(i + 1, min(i + 6, len(words))):
            if sent_text[words[k - 1].end:words[k].start].strip() or \
                    words[k].lower in ('ja', 'sillä', 'mutta', 'kun', 'joka',
                                       'eikä', 'tai', 'että', 'koska'):
                break  # seuraava lause ei kuulu kuten-jaksoon
            span.append(words[k])
        if not any(_finite_verb_any(_analyze(voikko, w.text, cache))
                   for w in span):
            continue  # verbiton jakso: "kuten aina", "kuten kuninkaalliset"
        out.append(Suggestion(
            rule='PUNCT_COMMA_KUTEN', category='style', severity='warning',
            start=offset + prev.end, end=offset + tok.start,
            message=('Kuten-jakso, joka sisältää verbin, erotetaan '
                     'päälauseesta pilkulla (", kuten").'),
            replacements=[', ']))
    return out


# Tasapainoisen sanaparin (mita-sita, toisaalta-toisaalta, milloin-milloin,
# osaksi-osaksi, yhtaalla-toisaalta) jasenet erotetaan toisistaan pilkulla:
# "Mita korkeammalla aurinko on, sita enemman altistumme." (ohjepankki,
# "Pilkku ja mita-sita, toisaalta-toisaalta", luettu 2026-11-25).
# Mita-sita-rakenne tunnistetaan vain, kun ensimmaisen jasenen joukossa on
# komparatiivi; muuten "mita ... sita" voi olla kysymys tai pronominiketju.

_PAIR_SECONDS = (('toisaalta', ('toisaalta', 'yhtäältä')),
                 ('milloin', ('milloin',)),
                 ('osaksi', ('osaksi',)))

def check_comma_mita_sita(sent_text, offset, words, voikko, cache):
    out = []

    def _missing_comma(j):
        prev = words[j - 1]
        gap = sent_text[prev.end:tok.start]
        return prev, gap.strip() == ''

    # mita-sita: virkkeen alkusanana "mita", myohemmin "sita" ilman pilkkua
    if words and words[0].lower == 'mitä':
        for j in range(2, len(words)):
            tok = words[j]
            if tok.lower != 'sitä':
                continue
            prev, missing = _missing_comma(j)
            if not missing:
                continue  # pilkku jo valissa
            seg = words[1:j]
            if not any(a.get('COMPARISON') == 'comparative'
                       for w in seg for a in _analyze(voikko, w.text, cache)):
                continue  # ei tasapainorakennetta: "Mita sita nyt tehtaisiin"
            out.append(Suggestion(
                rule='PUNCT_COMMA_MITA_SITA', category='style', severity='warning',
                start=offset + prev.end, end=offset + tok.start,
                message=('Tasapainoisen mitä–sitä-rakenteen jäsenet erotetaan '
                         'toisistaan pilkulla (", sitä").'),
                replacements=[', ']))
            break

    # muut parit: sanaparin toinen esiintyma ilman edeltavaa pilkkua
    for second, firsts in _PAIR_SECONDS:
        first_seen = False
        for i, tok in enumerate(words):
            if not first_seen and tok.lower in firsts:
                first_seen = True
                continue
            if first_seen and tok.lower == second:
                prev, missing = _missing_comma(i)
                if missing and prev.lower not in ('ja', 'sekä', 'tai', 'eli', 'mutta', 'vaan'):
                    out.append(Suggestion(
                        rule='PUNCT_COMMA_MITA_SITA', category='style',
                        severity='warning',
                        start=offset + prev.end, end=offset + tok.start,
                        message=('Tasapainoisen sanaparin jäsenet erotetaan '
                                 'toisistaan pilkulla (", %s").' % second),
                        replacements=[', ']))
                break
    return out


# Kiteytyneet sanaparit: eraat parit kirjoitetaan aina erilleen ("itse
# asiassa", ei "itseasiassa"), eraat aina yhteen ("edestakaisin", ei "edes
# takaisin"). Lahde: ohjepankki, "Yhdyssana vai ei: nurin pain vai nurinpain?
# - Kiteytyneet sanaparit" (luettu 2026-11-25). Listoihin on poimittu vain
# parit, joille sivu ei salli vaihtoehtoista kirjoitustapaa (ei ~-merkintaa).
# Erilleen-listassa ovat vain muodot, jotka Voikko hyvaksyy yhteen
# kirjoitettunakin, joten tavallinen oikeinkirjoitustarkistus ei niita tavoita.

_SANAPARI_APART = {
    'itseasiassa': 'itse asiassa',
    'kokoajan': 'koko ajan',
    'aikalailla': 'aika lailla',
    'kokolailla': 'koko lailla',
    'paikanpäällä': 'paikan päällä',
    'kaupanpäälle': 'kaupan päälle',
    'samantien': 'saman tien',
    'todenteolla': 'toden teolla',
    'ensikertaa': 'ensi kertaa',
    'vähänväliä': 'vähän väliä',
}

_SANAPARI_JOIN = {
    ('jälki', 'käteen'): 'jälkikäteen',
    ('poikki', 'päin'): 'poikkipäin',
    ('poikki', 'puolin'): 'poikkipuolin',
    ('poikki', 'teloin'): 'poikkiteloin',
}

def check_sanapari(sent_text, offset, words):
    out = []
    for i, tok in enumerate(words):
        fixed = _SANAPARI_APART.get(tok.lower)
        if fixed:
            if tok.text.isupper():
                repl = fixed.upper()
            elif tok.text[:1].isupper():
                repl = fixed.capitalize()
            else:
                repl = fixed
            out.append(Suggestion(
                rule='TYPO_SANAPARI', category='style', severity='warning',
                start=offset + tok.start, end=offset + tok.end,
                message=('Kiteytynyt sanapari kirjoitetaan erilleen: '
                         '"%s".' % fixed),
                replacements=[repl]))
            continue
        if i + 1 < len(words):
            nxt = words[i + 1]
            fixed = _SANAPARI_JOIN.get((tok.lower, nxt.lower))
            if fixed and sent_text[tok.end:nxt.start].strip() == '':
                if tok.text.isupper() and nxt.text.isupper():
                    repl = fixed.upper()
                elif tok.text[:1].isupper():
                    repl = fixed.capitalize()
                else:
                    repl = fixed
                out.append(Suggestion(
                    rule='TYPO_SANAPARI', category='style', severity='warning',
                    start=offset + tok.start, end=offset + nxt.end,
                    message=('Kiteytynyt sana kirjoitetaan yhteen: '
                             '"%s".' % fixed),
                    replacements=[repl]))
    return out


# Kun- ja kuin-konjunktioilla on yleiskielessa oma ydinkayttoalueensa:
# kun ilmaisee aikasuhdetta ("aina kun", "ennen kuin" on vertailu) ja kuin
# vertailua ("niin kuin", "sama kuin"). Tietyt sanaliitot ovat
# vaihtelemattomia; toiset (samaan aikaan kun/kuin, sita mukaa kun/kuin)
# sallivat molemmat ja ohitetaan. Lahde: ohjepankki, "Konjunktiot: kun vai
# kuin?" (luettu 2026-11-25). Vain suorat sanaparit ilman valimerkkia
# liputetaan.

_KUN_KUIN_TO_KUIN = {  # virhe: kun, oikein: kuin (vertailu)
    'aivan', 'ikään', 'niin', 'samoin',
    'sama', 'samaa', 'samanlainen', 'samanarvoinen',
    'erilainen', 'ennen',
}

_KUN_KUIN_TO_KUN = {  # virhe: kuin, oikein: kun (aikasuhde)
    'heti', 'silloin', 'sitten', 'asti', 'jälkeen', 'kerran',
}

def check_kun_kuin(sent_text, offset, words):
    out = []
    for i in range(len(words) - 1):
        tok, nxt = words[i], words[i + 1]
        if sent_text[tok.end:nxt.start].strip() != '':
            continue  # vain suoraan perakkaiset sanat
        if nxt.lower == 'kun' and tok.lower in _KUN_KUIN_TO_KUIN:
            out.append(Suggestion(
                rule='WORD_KUN_KUIN', category='style', severity='warning',
                start=offset + nxt.start, end=offset + nxt.end,
                message=('Vertailun sanaliitossa käytetään yleiskielessä '
                         'kuin-sanaa: "%s kuin".' % tok.lower),
                replacements=['kuin']))
        elif nxt.lower == 'kuin' and tok.lower in _KUN_KUIN_TO_KUN:
            out.append(Suggestion(
                rule='WORD_KUN_KUIN', category='style', severity='warning',
                start=offset + nxt.start, end=offset + nxt.end,
                message=('Aikaa ilmaisevassa sanaliitossa käytetään '
                         'yleiskielessä kun-sanaa: "%s kun".' % tok.lower),
                replacements=['kun']))
    return out


def run_rules(sent_text, offset, tokens, voikko, cache, before=''):
    words = [t for t in tokens if t.is_word]
    out = []
    out += check_double_word(sent_text, offset, words)
    out += check_negation(sent_text, offset, words, voikko, cache)
    out += check_negation_agreement(sent_text, offset, words)
    out += check_olla_agreement(sent_text, offset, words, voikko, cache)
    out += check_pron_verb_agreement(sent_text, offset, words, voikko, cache)
    out += check_sg_subject_plural_verb(
        sent_text, offset, words, voikko, cache, before)
    out += check_numeral_noun_case(sent_text, offset, words, voikko, cache)
    out += check_attribute_agreement(sent_text, offset, words, voikko, cache)
    out += check_comma_mutta_vaan(sent_text, offset, words, voikko, cache)
    out += check_comma_subordinate(sent_text, offset, words, voikko, cache)
    out += check_comma_relative(sent_text, offset, words, voikko, cache)
    out += check_comma_rinnastus(sent_text, offset, words, voikko, cache)
    out += check_comma_kuin(sent_text, offset, words, voikko, cache)
    out += check_comma_johtolause(sent_text, offset, words, voikko, cache)

    out += check_comma_lauseenvastike(sent_text, offset, words, voikko, cache)
    out += check_comma_list_ja(sent_text, offset, words, voikko, cache)
    out += check_comma_indirect_question(sent_text, offset, words, voikko, cache)
    out += check_comma_titles(sent_text, offset, words, voikko, cache)
    out += check_comma_kuten(sent_text, offset, words, voikko, cache)
    out += check_comma_mita_sita(sent_text, offset, words, voikko, cache)
    out += check_sanapari(sent_text, offset, words)
    out += check_kun_kuin(sent_text, offset, words)
    out += check_typography(sent_text, offset)
    out += check_lowercase_names(sent_text, offset, words, voikko, cache)
    out += check_active_perfect_passive_participle(
        sent_text, offset, words, voikko, cache)
    return out


# Pilkku mutta/vaan-konjunktion edella, kun jalkeen seuraa kokonainen
# paalause (ohjepankki, "Pilkku ja mutta, vaan", luettu 2026-11-22):
# "Arkisin salilla on hiljaista, mutta viikonloppuisin siella kay
# paljon asiakkaita." Kun mutta-jakso EI ole kokonainen paalause
# ("...mutta eivat ginsengjuurta"), pilkku on uuden saannon mukaan
# valinnainen -> ei liputeta. Tunnistus tarkkuus edella: heti
# mutta-sanan jalkeen nominatiivinen subjektiehdokas, jota seuraa
# suoraan finiittiverbi (tai kieltoverbi); muussa tapauksessa ohitus,
# joten esim. "mutta viikonloppuisin siella kay" jaa liputtamatta.


def _nom_subject(analyses):
    return any(a.get('SIJAMUOTO') == 'nimento'
               and a.get('CLASS') in ('nimisana', 'asemosana', 'etunimi',
                                      'sukunimi', 'paikannimi')
               and not a.get('PARTICIPLE')
               for a in analyses)


def _finite_person_verb(analyses):
    return any(a.get('CLASS') == 'teonsana' and a.get('PERSON') in ('1', '2', '3')
               and a.get('MOOD') in ('indicative', 'conditional', 'potential')
               and not a.get('PARTICIPLE') and not a.get('INFINITIVE')
               and a.get('NEGATIVE') not in ('true', True)
               for a in analyses)


def check_comma_mutta_vaan(sent_text, offset, words, voikko, cache):
    out = []
    for i, tok in enumerate(words):
        if tok.lower not in ('mutta', 'vaan') or i == 0:
            continue
        if ',' in sent_text[words[i - 1].end:tok.start]:
            continue  # pilkku on jo
        if i + 2 >= len(words):
            continue
        nxt = words[i + 1]
        if _neg_base(nxt.lower) in _KIELTO or nxt.lower.startswith('älä'):
            continue  # "mutta eivat ginsengjuurta": yhteinen subjekti
        subj_an = _analyze(voikko, nxt.text, cache)
        if not subj_an or not _nom_subject(subj_an):
            continue
        verb = words[i + 2]
        if _neg_base(verb.lower) not in _KIELTO and                 not _finite_person_verb(_analyze(voikko, verb.text, cache)):
            continue
        out.append(Suggestion(
            rule='PUNCT_COMMA_MUTTA_VAAN', category='style', severity='warning',
            start=offset + tok.start, end=offset + tok.end,
            message=('Kokonaisia päälauseita erottavan konjunktion "%s" '
                     'edellä on pilkku (", %s").' % (tok.text, tok.text)),
            replacements=[', ' + tok.text]))
    return out
