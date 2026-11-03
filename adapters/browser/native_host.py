#!/usr/bin/env python3
"""Punakynä native messaging -isäntä (selainsovitin, prototyyppi).

Arkkitehtuuri (valittu): selainlaajennos EI puhu HTTP:tä paikalliselle
rajapinnalle ollenkaan - ei CORS-ongelmia, ei Origin-kiertoja, tunnus ei
koskaan selaimen JavaScriptiin. Sen sijaan selain käynnistää tämän
isäntäprosessin ja puhuu kehystettyä JSON:ia stdio:lla (4-tavuinen LE-
pituus + UTF-8 JSON), kuten Chrome/Firefox native messaging määrittelee.

Enrollment: selaimen profiilihakemistoon rekisteröitävä isäntämanifesti
listaa sallitut laajennustunnukset (Chrome: allowed_origins,
Firefox: allowed_extensions) - se ON sovelluskohtainen valtuutus.
Peruutus = manifestin poisto (täysin palautettavissa, ei järjestelmämuutoksia).

Viestit:  {"text": "...", "use_rules": true, "use_spelling": true}
       -> {"suggestions": [...]} tai {"error": "..."}
"""
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from punakyna import client
from punakyna import tokenfile

MAX_MESSAGE = 2 * 1024 * 1024  # 2 MB


def read_message(stream):
    """Lue yksi kehys. Palauttaa None EOF:ssa (katkaistu/typistetty otsake).

    Heittaa ValueErrorin liian suuresta tai typistetysta rungosta.
    """
    header = stream.buffer.read(4)
    if len(header) < 4:
        return None  # EOF tai typistetty otsake: lopeta siististi
    (length,) = struct.unpack('<I', header)
    if length > MAX_MESSAGE:
        raise ValueError('liian suuri viesti')
    body = stream.buffer.read(length)
    if len(body) < length:
        raise ValueError('typistetty runko')
    return json.loads(body.decode('utf-8'))


def write_message(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
    stream.buffer.write(struct.pack('<I', len(data)) + data)
    stream.buffer.flush()


def main(api_port=8377):
    """Silmukka. stdout:hin kirjoitetaan VAIN protokollakehyksia -
    ei tracebackia, ei logitusta (stdout on selaimen kanava)."""
    # Sovelluskohtainen enrollment: PUNAKYNA_APP -> tokens/<app>
    # (luotu erikseen: python -m punakyna --enroll-app <app>). Ilman
    # muuttujaa kaytetaan perus-tunnusta taaksepain yhteensopivasti.
    app = os.environ.get('PUNAKYNA_APP')
    try:
        token = (tokenfile.read_app_token(app) if app
                 else client.read_token())
    except (FileNotFoundError, tokenfile.TokenError):
        # Ei tracebackia stdoutiin: se on selaimen protokollakanava.
        write_message(sys.stdout, {'error': 'ei rekisteroity: suorita '
                                   'python -m punakyna --enroll-app ' +
                                   (app or 'selain')})
        return 1
    while True:
        try:
            msg = read_message(sys.stdin)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            write_message(sys.stdout, {'error': 'virheellinen viesti'})
            continue
        if msg is None:
            return 0
        if not isinstance(msg, dict) or not isinstance(msg.get('text'), str):
            write_message(sys.stdout, {'error': 'odotettiin {"text": "..."}'})
            continue
        try:
            suggs = client.check(
                msg['text'], port=api_port, token=token,
                use_rules=msg.get('use_rules', True),
                use_spelling=msg.get('use_spelling', True))
            write_message(sys.stdout, {'suggestions': suggs})
        except Exception:
            # Ei poikkeustekstia ulos: saattaisi sisaltaa tekstikatkelmia.
            write_message(sys.stdout, {'error': 'tarkistus epaonnistui'})


if __name__ == '__main__':
    sys.exit(main())
