"""Opt-in debug logging and rendering experiments for the LibreOffice adapter.

Off by default. Enabled by ~/.config/punakyna/debug.json (read on every
call, so no restart is needed) or by PUNAKYNA_DEBUG=1 in the environment:

    {"log": true, "error_type": "spelling", "drop_suggestions": false}

log:              append every proofreading call to <tmpdir>/punakyna-debug.log
                  (includes the document text sent in, so keep it local).
error_type:       "proofreading" (default, grammar) or "spelling": reports our
                  findings as spelling-type errors, to test how LibreOffice
                  draws them in the Spelling dialog. Experiment only.
drop_suggestions: return findings without suggestions.
"""
import json
import os
import tempfile
import time
from pathlib import Path

MAX_LOG_BYTES = 5_000_000
TYPES = {'proofreading': 2, 'spelling': 1}


def log_path():
    return Path(tempfile.gettempdir()) / 'punakyna-debug.log'


def _config_path():
    base = os.environ.get('PUNAKYNA_CONFIG', '~/.config/punakyna')
    return Path(os.path.expanduser(base)) / 'debug.json'


def load_config():
    cfg = {'log': False, 'error_type': 'proofreading', 'drop_suggestions': False}
    if os.environ.get('PUNAKYNA_DEBUG') == '1':
        cfg['log'] = True
    try:
        data = json.loads(_config_path().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return cfg
    if isinstance(data, dict):
        if isinstance(data.get('log'), bool):
            cfg['log'] = data['log']
        if data.get('error_type') in TYPES:
            cfg['error_type'] = data['error_type']
        if isinstance(data.get('drop_suggestions'), bool):
            cfg['drop_suggestions'] = data['drop_suggestions']
    return cfg


def error_type_value(cfg, default):
    """TextMarkupType value to use; `default` when no experiment is set."""
    if cfg['error_type'] == 'proofreading':
        return default
    return TYPES[cfg['error_type']]


def log_call(cfg, text, start, end, errors, version=''):
    """Append one JSON line. Never raises."""
    if not cfg.get('log'):
        return
    try:
        p = log_path()
        if p.exists() and p.stat().st_size > MAX_LOG_BYTES:
            p.write_text('', encoding='utf-8')
        rec = {'t': time.strftime('%Y-%m-%dT%H:%M:%S'), 'version': version,
               'config': {k: cfg[k] for k in ('error_type', 'drop_suggestions')},
               'text': text, 'sentence_start': start, 'sentence_end': end,
               'errors': errors}
        with p.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    except Exception:
        pass
