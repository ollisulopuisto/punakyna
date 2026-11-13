"""LO_ENV-puhdistus tunnistaa virtualenvit rakenteesta, ei .venv-nimesta."""
import os
import sys

from lo_env import clean_lo_env


def _make_venv(root):
    bindir = root / 'bin'
    bindir.mkdir(parents=True)
    (root / 'pyvenv.cfg').write_text('home = /usr/bin\n')
    (bindir / 'python3').write_text('')
    return str(bindir)


def test_drops_venv_with_custom_name(tmp_path):
    venv_bin = _make_venv(tmp_path / 'my-env')
    env = clean_lo_env({'PATH': os.pathsep.join([venv_bin, '/usr/bin'])},
                       prefix='/usr', base_prefix='/usr')
    assert env['PATH'] == '/usr/bin'


def test_drops_virtual_env_var_and_its_bin(tmp_path):
    root = tmp_path / 'elsewhere'
    (root / 'bin').mkdir(parents=True)  # ei pyvenv.cfg:aa
    env = clean_lo_env({'PATH': os.pathsep.join([str(root / 'bin'), '/usr/bin']),
                        'VIRTUAL_ENV': str(root)},
                       prefix='/usr', base_prefix='/usr')
    assert env['PATH'] == '/usr/bin'
    assert 'VIRTUAL_ENV' not in env


def test_drops_active_prefix_when_in_venv(tmp_path):
    root = tmp_path / 'pfx'
    (root / 'bin').mkdir(parents=True)
    env = clean_lo_env({'PATH': os.pathsep.join([str(root / 'bin'), '/usr/bin'])},
                       prefix=str(root), base_prefix='/usr')
    assert env['PATH'] == '/usr/bin'


def test_keeps_system_dirs(tmp_path):
    sysbin = tmp_path / 'sys' / 'bin'
    sysbin.mkdir(parents=True)
    path = os.pathsep.join([str(sysbin), '/usr/bin'])
    env = clean_lo_env({'PATH': path}, prefix='/usr', base_prefix='/usr')
    assert env['PATH'] == path


def test_running_interpreter_venv_not_left_on_path():
    env = clean_lo_env()
    if sys.prefix != sys.base_prefix:
        for p in env['PATH'].split(os.pathsep):
            assert not os.path.realpath(p).startswith(
                os.path.realpath(sys.prefix) + os.sep)
