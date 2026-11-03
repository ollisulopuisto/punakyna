"""Kokeellinen parsitun tason mittaus (Ei osa julkaistavaa pakettia).

Tarkoitus: mitata, korjaako Stanza-pohjainen (fin_tdt) jäsentävä taso
dokumentoidut virheluokat ilman yliliputuksen kasvua:
  1. et/että-puhekielianalysi (NEG_CONNEGATIVE väärät osumat)
  2. verbiketjut ("ei voisi maksaa")
  3. eksistentiaalilauseen partitiivisubjekti (SV_AGREEMENT väärät paritukset)
  4. persoonakongruenssi (MultiBLiMP SV-P, jota sääntötaso ei kata)

Protokolla: säännöt kalibroitu vain dev-puolikkaalla (parilliset indeksit);
held-puolikas (parittomat) ajetaan kerran. Kaikki luvut kehitysvaiheen
mittauksia - eivät todistusta ylivoimasta. Jäädytetty baseline säilyy.
Latenssi: Linux-hiekkalaatikko, EI Mac-todiste.

Mallit: stanza (Apache-2.0-koodi) + fin_tdt-malli (UD_Finnish-TDT, CC BY-SA 4.0
-jakeluun liittyvät ehdot selvitettävä ennen paketointia).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stanza  # noqa: E402

from punakyna.backend_voikko import get_voikko  # noqa: E402


def voikko_participle_number(text):
    for a in get_voikko().analyze(text):
        if a.get('PARTICIPLE') == 'past_active':
            return a.get('NUMBER')
    return None

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = stanza.Pipeline('fi', package='tdt',
                               processors='tokenize,mwt,pos,lemma,depparse',
                               use_gpu=False, verbose=False)
    return _nlp


def feats(word):
    d = {}
    if word.feats:
        for kv in word.feats.split('|'):
            k, v = kv.split('=', 1)
            d[k] = v
    return d


def parse_rules(doc):
    """Palauta ehdotukset: (sääntö, lauseen_id, sana, viesti)."""
    out = []
    for si, sent in enumerate(doc.sentences):
        words = sent.words
        by_id = {w.id: w for w in words}
        # nsubj -> pääsana -kartta
        for w in words:
            f = feats(w)
            if w.deprel and w.deprel.startswith('nsubj'):
                head = by_id.get(w.head)
                if head is None or head.upos not in ('VERB', 'AUX'):
                    continue
                hf = feats(head)
                if hf.get('Voice') == 'Pass':
                    continue
                if f.get('Case') == 'Par':
                    continue  # eksistentiaalilauseen partitiivi: yksikkö OK
                if f.get('Number') == 'Plur' and f.get('Case') == 'Nom' \
                        and hf.get('Number') == 'Sing' and hf.get('Person') not in (None, '0'):
                    out.append(('PSV_NUMBER', si, head.text,
                                f'monikollinen subjekti "{w.text}" + yksiköllinen verbi "{head.text}"'))
                if f.get('Person') in ('1', '2', '3') and hf.get('Person') in ('1', '2', '3') \
                        and f['Person'] != hf['Person']:
                    out.append(('PSV_PERSON', si, head.text,
                                f'subjektin "{w.text}" persoona {f["Person"]} != verbin "{head.text}" {hf["Person"]}'))
            # PSV_NECESSIVE POISTETTU: VISK §1581 esimerkit ("Turvavyot on
            # pidettava", "Avaimet on palautettava") osoittavat rakenteen
            # olevan vakiosuomea - ei kongruenssivirhe.
            # kieltoverbi -> pääverbi konnegatiivitarkistus
            if f.get('Polarity') == 'Neg':
                head = by_id.get(w.head)
                if head is None or head.upos not in ('VERB', 'AUX'):
                    continue
                # perfektiketju: "emme ole nähnyt" - laskeudu partisiippiin
                while head.lemma == 'olla' and feats(head).get('VerbForm') == 'Fin':
                    nxt = by_id.get(head.head)
                    if nxt is None or nxt.upos not in ('VERB', 'AUX'):
                        break
                    head = nxt
                hf = feats(head)
                if hf.get('VerbForm') == 'Part':
                    # lukukongruenssi: emme/ette/eivät vaativat monikon;
                    # jäsentimen LUKU-piirre normalisoituu virheessä ->
                    # varmista partisiipin luku Voikolla
                    if f.get('Number') == 'Plur' and hf.get('PartForm') == 'Past':
                        vn = voikko_participle_number(head.text)
                        if vn == 'singular':
                            out.append(('PNEG_NUMBER', si, head.text,
                                        f'monikollinen kieltoverbi "{w.text}" + yksiköllinen partisiippi "{head.text}"'))
                elif hf.get('VerbForm') == 'Fin':
                    # preesens: finiittimuoto konnegatiivina (henkilötunnottomat
                    # muodot kuten "pelaa" ovat oikein); liputa vain jos muoto
                    # on selvästi persoonallinen JA eroaa kieltoverbin henkilöstä
                    if hf.get('Person') in ('1', '2', '3') and hf.get('Person') != f.get('Person'):
                        out.append(('PNEG_CONNEG', si, head.text,
                                    f'kieltoverbin "{w.text}" jälkeen persoonallinen muoto "{head.text}"'))
                elif hf.get('VerbForm') == 'Inf':
                    pass  # "ei voinut maksaa": ketju OK
    return out


def check(text):
    doc = get_nlp()(text)
    return parse_rules(doc)


if __name__ == '__main__':
    for t in ['Mä en huomannu, et sulla on kassi.',
              'Tietoja on kertynyt.',
              'Tällaiset valvontatiedot on asetettava saataville.',
              'Minä näkee hänet.',
              'Emme ole nähneet sitä.',
              'Emme ole nähnyt sitä.',
              'Ei se paljoo välitä.']:
        print(t, '->', check(t))
