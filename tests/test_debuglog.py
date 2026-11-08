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


def test_log_file_private_capped_and_symlink_safe(tmp_path, monkeypatch):
    import os, stat
    monkeypatch.setattr(debuglog.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(debuglog, 'MAX_LOG_BYTES', 2000)
    cfg = {'log': True, 'error_type': 'proofreading', 'drop_suggestions': False}
    p = tmp_path / 'punakyna-debug.log'
    p.write_text('old\n')
    os.chmod(p, 0o644)
    debuglog.log_call(cfg, 'a', 0, 1, [], note='n')
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    for _ in range(30):
        debuglog.log_call(cfg, 'x' * 300, 0, 1, [])
        assert p.stat().st_size <= 2000
    debuglog.log_call(cfg, 'y' * 5000, 0, 1, [])
    assert 'record too large' in p.read_text().splitlines()[-1]
    assert p.stat().st_size <= 2000
    p.unlink()
    target = tmp_path / 'victim'
    target.write_text('keep')
    p.symlink_to(target)
    debuglog.log_call(cfg, 'z', 0, 1, [])
    assert target.read_text() == 'keep'


def test_malformed_values_do_not_break_other_options(tmp_path, monkeypatch):
    monkeypatch.setenv('PUNAKYNA_CONFIG', str(tmp_path))
    (tmp_path / 'debug.json').write_text(json.dumps(
        {'log': True, 'error_type': ['x'], 'drop_suggestions': True}))
    cfg = debuglog.load_config()
    assert cfg['log'] and cfg['drop_suggestions'] and cfg['error_type'] == 'proofreading'
