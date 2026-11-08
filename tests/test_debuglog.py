import json
from punakyna import debuglog


def test_off_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv('PUNAKYNA_CONFIG', str(tmp_path))
    monkeypatch.delenv('PUNAKYNA_DEBUG', raising=False)
    cfg = debuglog.load_config()
    assert cfg == {'log': False, 'error_type': 'proofreading', 'drop_suggestions': False}
    assert debuglog.error_type_value(cfg, 2) == 2


def test_config_file_and_bad_values(tmp_path, monkeypatch):
    monkeypatch.setenv('PUNAKYNA_CONFIG', str(tmp_path))
    (tmp_path / 'debug.json').write_text(json.dumps(
        {'log': True, 'error_type': 'spelling', 'drop_suggestions': 'x'}))
    cfg = debuglog.load_config()
    assert cfg['log'] and cfg['error_type'] == 'spelling' and not cfg['drop_suggestions']
    assert debuglog.error_type_value(cfg, 2) == 1
    (tmp_path / 'debug.json').write_text('not json')
    assert debuglog.load_config()['log'] is False


def test_log_writes_json_line_and_never_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(debuglog.tempfile, 'gettempdir', lambda: str(tmp_path))
    cfg = {'log': True, 'error_type': 'proofreading', 'drop_suggestions': False}
    debuglog.log_call(cfg, 'Minä olemme', 0, 11, [{'start': 5}], '0.1.10')
    rec = json.loads((tmp_path / 'punakyna-debug.log').read_text().splitlines()[0])
    assert rec['text'] == 'Minä olemme' and rec['errors'][0]['start'] == 5
    cfg['log'] = False
    debuglog.log_call(cfg, 'x', 0, 1, [])
    assert len((tmp_path / 'punakyna-debug.log').read_text().splitlines()) == 1
    monkeypatch.setattr(debuglog.tempfile, 'gettempdir', lambda: '/nonexistent/x')
    cfg['log'] = True
    debuglog.log_call(cfg, 'x', 0, 1, [])
