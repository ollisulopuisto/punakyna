"""Puhdistettu ymparisto LibreOffice-valiprosesseille (unopkg/soffice).

LO:n python-tarjoaja kaatuu std::bad_alloc:iin, jos PATH:in ensimmainen
python kuuluu virtualenviin. Virtualenv tunnistetaan rakenteesta, ei
nimesta: hakemisto, jonka vanhemmassa on pyvenv.cfg, VIRTUAL_ENV:n tai
nykyisen virtuaaliympariston (sys.prefix != sys.base_prefix) alla oleva
hakemisto pudotetaan PATH:ista.
"""
import os
import sys


def _under(path, root):
    if not root:
        return False
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def is_venv_dir(entry, environ=None, prefix=None, base_prefix=None):
    environ = os.environ if environ is None else environ
    prefix = sys.prefix if prefix is None else prefix
    base_prefix = sys.base_prefix if base_prefix is None else base_prefix
    if not entry:
        return False
    if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(entry)),
                                   'pyvenv.cfg')):
        return True
    if _under(entry, environ.get('VIRTUAL_ENV')):
        return True
    return prefix != base_prefix and _under(entry, prefix)


def clean_lo_env(environ=None, prefix=None, base_prefix=None):
    env = dict(os.environ if environ is None else environ)
    env.pop('VIRTUAL_ENV', None)
    kept = [p for p in env.get('PATH', '').split(os.pathsep)
            if not is_venv_dir(p, environ=(os.environ if environ is None
                                           else environ),
                               prefix=prefix, base_prefix=base_prefix)]
    env['PATH'] = os.pathsep.join(kept)
    return env
