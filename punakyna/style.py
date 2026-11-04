"""Optional Finnish style prompts, not grammar errors or automatic rewrites.

Sources and limits: docs/style-advice.md. No network/model calls.
"""
from dataclasses import dataclass
import re
from .rules import Suggestion


@dataclass(frozen=True)
class StyleProfile:
    prefer_active: bool = False
    narrator: str = 'any'  # any | mina | me
    reader: str = 'any'    # any | sina | te

    @classmethod
    def from_value(cls, value):
        if value is None:
            return cls()
        if isinstance(value, cls):
            value.validate()
            return value
        if not isinstance(value, dict) or set(value) - {'prefer_active', 'narrator', 'reader'}:
            raise ValueError('invalid style profile')
        p = cls(**value)
        p.validate()
        return p

    def validate(self):
        if (type(self.prefer_active) is not bool
                or self.narrator not in ('any', 'mina', 'me')
                or self.reader not in ('any', 'sina', 'te')):
            raise ValueError('invalid style profile')

    @property
    def enabled(self):
        return self.prefer_active or self.narrator != 'any' or self.reader != 'any'


# Conservative exclusion: whole sentences containing quotation/code delimiters
# are skipped. A fragmentary quotation must not change the apparent narrator.
_QUOTED = re.compile(r'["“”«»`]|(?:^|\n)\s*[>–—]')
_PERSON_WORDS = {'minä': ('1', 'singular'), 'me': ('1', 'plural'),
                 'sinä': ('2', 'singular'), 'te': ('2', 'plural')}
_LABELS = {'mina': 'minä', 'me': 'me', 'sina': 'sinä', 'te': 'te'}


def excluded_text(text):
    return bool(_QUOTED.search(text) or re.search(r"[{}]|https?://|www\.", text))


def check_style(sentence, offset, tokens, voikko, cache, profile):
    profile = StyleProfile.from_value(profile)
    if not profile.enabled or excluded_text(sentence):
        return []
    out = []
    flagged_roles = set()
    for tok in tokens:
        if not tok.is_word:
            continue
        if tok.text not in cache:
            cache[tok.text] = voikko.analyze(tok.text)
        analyses = cache[tok.text]
        verbs = [a for a in analyses if a.get('CLASS') == 'teonsana'
                 and a.get('PERSON') and a.get('MOOD') not in ('A-infinitive', 'E-infinitive', 'MA-infinitive')]
        # Only morphologically unanimous passive finite forms. Ambiguous
        # imperative/passive homographs (e.g. lähetä) are intentionally skipped.
        if (profile.prefer_active and verbs and len(verbs) == len(analyses)
                and all(a.get('PERSON') == '4' for a in verbs)):
            out.append(Suggestion('STYLE_ACTOR', 'style', 'style',
                offset + tok.start, offset + tok.end,
                'Tyylivinkki: harkitse tekijän ilmaisemista aktiivimuodolla, jos lukijan pitää tietää, kuka toimii. Passiivi voi olla tässä tarkoituksenmukainen.', []))
        person = _PERSON_WORDS.get(tok.lower)
        if person is None and verbs and len(verbs) == len(analyses):
            values = {(a.get('PERSON'), a.get('NUMBER')) for a in verbs}
            if len(values) == 1:
                person = next(iter(values))
        if person is None:
            # Possessive suffixes only when every analysis agrees. Do not
            # infer a narrator from noun/verb ambiguities such as voimme.
            suffixes = {a.get('POSSESSIVE') for a in analyses}
            if len(suffixes) == 1:
                suffix = next(iter(suffixes))
                person = {'1s': ('1','singular'), '1p': ('1','plural'),
                          '2s': ('2','singular'), '2p': ('2','plural')}.get(suffix)
        choice = profile.narrator if person and person[0] == '1' else profile.reader if person and person[0] == '2' else 'any'
        expected = {'mina': 'singular', 'me': 'plural', 'sina': 'singular', 'te': 'plural'}.get(choice)
        if expected and person[1] != expected and person[0] not in flagged_roles:
            flagged_roles.add(person[0])
            role = 'kertojan' if person[0] == '1' else 'lukijan puhuttelun'
            out.append(Suggestion('STYLE_PERSON', 'style', 'style',
                offset + tok.start, offset + tok.end,
                'Tyylivinkki: valittu %s muoto on %s. Tarkista, viittaako tämä ilmaus samaan henkilöön tai ryhmään. Kyse voi olla tarkoituksellisesta näkökulman vaihdosta.' % (role, _LABELS[choice]), []))
    return out
