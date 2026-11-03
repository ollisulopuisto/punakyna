"""Punakynä-LibreOffice-sovitin (prototyyppi, EI asennettava laajennos).

Lukee avoimen Writer-asiakirjan kappaleet UNO-sillan yli ja tarkistaa ne
paikallisella Punakynä-rajapinnalla (teksti pysyy koneella). Tulostaa
löydökset kappaleindekseillä. Ajetaan LibreOfficen rinnalla:

  soffice --headless --accept='socket,host=127.0.0.1,port=2002;urp;' &
  python3 punakyna_lo.py --port 2002 --api-port 8377

Validointitaso: todellinen LibreOffice Linuxissa (headless). EI vastaa
Mac-asennusta tai paketoitua .oxt-laajennosta.
"""
import argparse
import json
import sys
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue


def connect(port):
    ctx = uno.getComponentContext()
    resolver = ctx.ServiceManager.createInstanceWithContext(
        'com.sun.star.bridge.UnoUrlResolver', ctx)
    return resolver.resolve(
        f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext')


from offsets import py_offset_to_uno  # sama hakemisto; ei UNO-riippuvuutta


WAVE_UNDERLINE = 10   # com.sun.star.awt.FontUnderline.WAVE
SINGLE_UNDERLINE = 1
PROPS = ('CharUnderline', 'CharUnderlineColor', 'CharUnderlineHasColor')
STATE_PATH = Path.home() / '.config' / 'punakyna' / 'lo-highlights.json'


def iter_paragraphs(doc):
    """Tuottaa (index, teksti, elementti) asiakirjan leipätekstin kappaleille."""
    enum = doc.Text.createEnumeration()
    i = 0
    while enum.hasMoreElements():
        para = enum.nextElement()
        if para.supportsService('com.sun.star.text.Paragraph'):
            yield i, para.getString(), para
            i += 1


def highlight_range(doc, para, para_idx, start_cp, end_cp, originals):
    """Korosta kohta (aaltoalleviivaus, punainen). MUTTAA asiakirjan
    muotoilua: tallentaa alkuperäiset ominaisuudet originals-listaan
    tarkan palautuksen mahdollistamiseksi. Ei muuta tekstiä.

    start_cp/end_cp ovat Python-koodipisteindeksejä kappaleen tekstissä.
    HUOM (mitattu LO 7.3): cursor.goRight laskee KOODIPISTEITÄ, ei
    UTF-16-yksiköitä - emoji siirtää vain yhdellä. Tekstirakenteiden
    merkkipositiot (esim. API-paluurvot) ovat sen sijaan UTF-16-yksiköitä:
    muunnos niiden kanssa offsets.py_offset_to_uno:lla.
    """
    cursor = doc.Text.createTextCursorByRange(para.Start)
    cursor.goRight(start_cp, False)
    cursor.goRight(end_cp - start_cp, True)
    originals.append({
        'para': para_idx, 'start': start_cp, 'end': end_cp,
        'text': cursor.getString(),
        'props': {p: getattr(cursor, p) for p in PROPS},
    })
    try:
        cursor.CharUnderline = WAVE_UNDERLINE
    except Exception:
        cursor.CharUnderline = SINGLE_UNDERLINE
    cursor.CharUnderlineColor = 0xFF0000
    cursor.CharUnderlineHasColor = True


def _para_by_index(doc, wanted):
    for idx, _text, para in iter_paragraphs(doc):
        if idx == wanted:
            return para
    return None


def restore_highlights(doc, records):
    """Palauta TASAN ne ominaisuudet, jotka olivat voimassa ennen
    korostusta. Jos teksti kohdalla on muuttunut (käyttäjä editoinut),
    ohita ja varoita - älä koske vääriin kohtiin."""
    skipped = 0
    for rec in records:
        para = _para_by_index(doc, rec['para'])
        if para is None:
            skipped += 1
            continue
        cursor = doc.Text.createTextCursorByRange(para.Start)
        cursor.goRight(rec['start'], False)
        cursor.goRight(rec['end'] - rec['start'], True)
        if cursor.getString() != rec['text']:
            skipped += 1
            print(f'varoitus: kappaleen {rec["para"]} kohta muuttunut '
                  f'(oli {rec["text"]!r}) - jätetään palauttamatta',
                  file=sys.stderr)
            continue
        for p, v in rec['props'].items():
            setattr(cursor, p, v)
    return skipped


def load_state(path=STATE_PATH):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_state(records, path=STATE_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=2002, help='LO UNO -portti')
    ap.add_argument('--api-port', type=int, default=8377, help='Punakynä-portti')
    ap.add_argument('--token-path', default=None)
    ap.add_argument('--highlight', action='store_true',
                    help='korosta löydökset asiakirjaan (aaltoalleviivaus)')
    ap.add_argument('--clear', action='store_true',
                    help='poista korostukset ja lopeta')
    args = ap.parse_args()

    sys.path.insert(0, '.')
    from punakyna import client

    token = client.read_token(args.token_path) if args.token_path else client.read_token()
    ctx = connect(args.port)
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    doc = desktop.getCurrentComponent()
    if doc is None:
        print('Ei avointa asiakirjaa.', file=sys.stderr)
        return 1

    if args.clear:
        records = load_state()
        if not records:
            print('Ei tallennettuja korostuksia.')
            return 0
        skipped = restore_highlights(doc, records)
        save_state([])
        print(f'Korostukset poistettu ({len(records) - skipped} palautettu, '
              f'{skipped} ohitettu muutoksen vuoksi).')
        return 0

    originals = load_state()
    if originals:
        # toistuva ajo: palauta edellisen ajon korostukset ensin
        # (muuten 'alkuperäiseksi' tallentuisi oma korostuksemme)
        restore_highlights(doc, originals)
        originals = []
    found = 0
    for idx, text, para in iter_paragraphs(doc):
        if not text.strip():
            continue
        for s in client.check(text, port=args.api_port, token=token):
            found += 1
            if args.highlight:
                highlight_range(doc, para, idx, s['start'], s['end'], originals)
            u0, u1 = py_offset_to_uno(text, s['start']), py_offset_to_uno(text, s['end'])
            print(f'kappale {idx}, merkit {s["start"]}-{s["end"]} '
                  f'(UTF-16: {u0}-{u1}) [{s["rule"]}] {s["message"]}')
    if args.highlight and found:
        save_state(originals)
        print('HUOM: korostus muuttaa asiakirjan MUOTOILUA (ei tekstiä). '
              'Palautus: --clear. Oikea integraatioreitti myöhemmin: '
              'UNO XProofreader-palvelu (ei muotoilua).', file=sys.stderr)
    print(f'Yhteensä {found} löydöstä.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
