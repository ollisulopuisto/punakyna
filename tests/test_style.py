from punakyna.pipeline import check_text
from types import SimpleNamespace
from punakyna.style import StyleProfile, check_style
import pytest


class Analyzer:
    def __init__(self, mapping):
        self.mapping = mapping
    def analyze(self, word):
        return self.mapping.get(word, [])


def check(text, morphology, **profile):
    word = text.strip('"“”`')
    token = SimpleNamespace(text=word, lower=word.lower(), start=0, end=len(word), is_word=True)
    return check_style(text, 0, [token], Analyzer({word: morphology}), {}, profile)


def verb(person, number=None):
    return dict(CLASS='teonsana', PERSON=person, NUMBER=number, MOOD='indicative')


def test_off_by_default():
    assert check('haetaan', [verb('4')]) == []


def test_passive_advisory_never_rewrites():
    r = check('haetaan', [verb('4')], prefer_active=True)
    assert len(r) == 1 and r[0].severity == 'style'
    assert r[0].replacements == [] and 'Passiivi voi' in r[0].message


def test_ambiguous_passive_imperative_skipped():
    assert check('lähetä', [verb('4'), verb('2','singular')], prefer_active=True) == []


def test_narrator_role_does_not_ban_reader():
    assert check('voitte', [verb('2','plural')], narrator='mina') == []
    assert check('me', [], narrator='mina')[0].rule == 'STYLE_PERSON'


def test_reader_consistency_and_quoted_exclusion():
    assert check('voitte', [verb('2','plural')], reader='sina')[0].severity == 'style'
    assert check('“voitte”', [verb('2','plural')], reader='sina') == []
    assert check('voit', [verb('2','singular')], reader='sina') == []


def test_other_actor_and_ambiguous_analysis_exempt():
    assert check('hakee', [verb('3','singular')], reader='sina') == []
    assert check('voimme', [verb('1','plural'), dict(CLASS='nimisana')], narrator='mina') == []


def test_invalid_profile_rejected():
    for value in [True, {'reader':'he'}, {'prefer_active':'yes'}, {'remote':True}]:
        with pytest.raises(ValueError):
            StyleProfile.from_value(value)


def test_settings_roundtrip_and_corruption(monkeypatch, tmp_path):
    from punakyna.style_settings import load_profile, save_profile, settings_path
    monkeypatch.setenv('PUNAKYNA_CONFIG', str(tmp_path))
    assert not load_profile().enabled
    profile = StyleProfile(True, 'me', 'sina')
    save_profile(profile)
    assert load_profile() == profile
    settings_path().write_text('{broken', encoding='utf-8')
    assert not load_profile().enabled


def test_quotes_code_and_urls_skipped():
    from punakyna.style import excluded_text
    for text in ['“Lainaus. Vielä lainauksessa.”', '```haetaan```', '> haetaan', '{haetaan}', 'https://example.com']:
        assert excluded_text(text)


def test_native_pipeline_default_and_roles():
    from punakyna.pipeline import check_text
    def rules(text, **p):
        return [s.rule for s in check_text(text, use_rules=False, use_spelling=False, use_gc=False, style_profile=p)]
    assert rules('Hakemus lähetetään huomenna.') == []
    assert rules('Hakemus lähetetään huomenna.', prefer_active=True) == ['STYLE_ACTOR']
    assert rules('Me lähetämme hakemuksen sinulle.', narrator='me', reader='sina') == []
    assert rules('Voitte lähettää hakemuksen.', reader='sina') == ['STYLE_PERSON']
    assert rules('Lähetä hakemus.', prefer_active=True) == []
    assert rules('”Hakemus lähetetään. Se käsitellään.”', prefer_active=True) == []


def test_style_never_suppresses_grammar(monkeypatch):
    import punakyna.pipeline as pipeline
    from punakyna.rules import Suggestion
    monkeypatch.setattr(pipeline, '_voikko_gc_suggestions', lambda text: [
        Suggestion('GRAMMAR', 'grammar', 'error', 8, 18, 'grammar')])
    result = pipeline.check_text('Hakemus lähetetään huomenna.', use_rules=False, use_spelling=False,
                                 style_profile={'prefer_active': True})
    assert [s.rule for s in result] == ['GRAMMAR']


def test_person_hint_once_per_role():
    from punakyna.pipeline import check_text
    result = check_text('Me lähetämme hakemuksen.', use_spelling=False, use_rules=False, use_gc=False,
                        style_profile={'narrator': 'mina'})
    assert [s.rule for s in result] == ['STYLE_PERSON']


def test_oxt_contains_style_components(tmp_path):
    import importlib.util
    from pathlib import Path
    import zipfile
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('pack_style', root/'adapters/libreoffice/xproofreader/make_oxt.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path = tmp_path/'style.oxt'
    mod.build(path)
    with zipfile.ZipFile(path) as z:
        assert {'punakyna/style.py', 'punakyna/style_settings.py', 'punakyna_style_settings.py', 'Addons.xcu'} <= set(z.namelist())
        assert b'punakyna_style_settings.py' in z.read('META-INF/manifest.xml')


def test_cli_style_server_defaults(monkeypatch):
    import punakyna.api as api
    from punakyna.cli import main
    captured = {}
    monkeypatch.setattr(api, 'serve', lambda **kw: captured.update(kw))
    main(['--serve', '--prefer-active', '--narrator', 'me'])
    assert captured['style_profile'] == {'prefer_active': True, 'narrator': 'me', 'reader': 'any',
                                         'max_sentence_words': 0}
    main(['--serve', '--profile', 'virkakieli'])
    assert captured['style_profile'] == {'prefer_active': True, 'narrator': 'any',
                                         'reader': 'any', 'max_sentence_words': 15}


def test_sentence_length_hint_is_opt_in_and_cited():
    from punakyna.style import StyleProfile
    # 24 sanaa (oma lause, ei Kotuksen esimerkkilausetta)
    long_s = ('Jos lapsen hoidon tarpeen ajankohtaa ei voi ennakoida ja paikan tarve johtuu '
              'äkillisestä työllistymisestä tai opiskelupaikan saamisesta, paikkaa on haettava '
              'niin pian kuin mahdollista.')
    assert not [s for s in check_text(long_s, use_spelling=False)
                if s.rule == 'STYLE_SENTENCE_LENGTH']
    hits = [s for s in check_text(long_s, use_spelling=False,
                                  style_profile={'max_sentence_words': 15})
            if s.rule == 'STYLE_SENTENCE_LENGTH']
    assert len(hits) == 1 and hits[0].severity == 'style'
    assert long_s[hits[0].start:hits[0].end] == 'opiskelupaikan'  # 16. sana
    assert not [s for s in check_text('Tämä on lyhyt virke.', use_spelling=False,
                                      style_profile={'max_sentence_words': 15})
                if s.rule == 'STYLE_SENTENCE_LENGTH']
    assert StyleProfile.preset('virkakieli').max_sentence_words == 15
    assert StyleProfile.preset('standard') == StyleProfile()


def test_sentence_length_validation():
    import pytest
    from punakyna.style import StyleProfile
    for bad in (-1, 201, True, '15', 1.5):
        with pytest.raises(ValueError):
            StyleProfile.from_value({'max_sentence_words': bad})
