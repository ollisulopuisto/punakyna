#!/usr/bin/env python3
"""Opt-in real macOS LibreOffice host smoke. Never touches the user profile.

Pass the FINISHED OXT and a Python executable with LibreOffice's uno module.
This checks the native host callback and programmatic replacement, not F7 UI.
It must run on an arm64 Mac; a skipped/unrun invocation is not a passing gate.
"""
import argparse
import os
from pathlib import Path
import platform
import socket
import subprocess
import tempfile
import time

CHECK = r'''
import time, uno
from com.sun.star.lang import Locale
resolver = uno.getComponentContext().ServiceManager.createInstanceWithContext(
    'com.sun.star.bridge.UnoUrlResolver', uno.getComponentContext())
ctx = resolver.resolve('uno:socket,host=127.0.0.1,port=PORT;urp;StarOffice.ComponentContext')
sm = ctx.ServiceManager
desktop = sm.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, ())
text = 'Puhelinnumerosi on vaihdettu. Vahvista uusi numerosi syöttämälllä seuraava vahvistuskoodi: 000000.'
c = doc.Text.createTextCursor()
c.CharLocale = Locale('fi', 'FI', '')
doc.Text.insertString(c, text, False)
# Give the actual host background iterator a chance to load the dylibs.
time.sleep(5)
proof = sm.createInstanceWithContext('org.punakyna.comp.pyuno.PunakynaProofreader', ctx)
r = proof.doProofreading('regression', text, Locale('fi', 'FI', ''), 0, len(text), ())
hits = [e for e in r.aErrors if e.aRuleIdentifier == 'punakyna.SPELL' and 'syöttämällä' in e.aSuggestions]
assert hits, [(e.aRuleIdentifier, e.aSuggestions) for e in r.aErrors]
e = hits[0]
c = doc.Text.createTextCursor()
c.gotoStart(False)
c.goRight(e.nErrorStart, False)
c.goRight(e.nErrorLength, True)
c.String = 'syöttämällä'
assert 'syöttämälllä' not in doc.Text.String
assert 'syöttämällä' in doc.Text.String
# Repeat real UNO callbacks; the reported crash was in GrammarCheckingIterator.
for _ in range(20):
    proof.doProofreading('regression', text, Locale('fi', 'FI', ''), 0, len(text), ())
doc.close(True)
print('MAC_HOST_CALLBACK_AND_PROGRAMMATIC_REPLACEMENT_PASS')
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--oxt', required=True, type=Path)
    p.add_argument('--uno-python', required=True, type=Path)
    p.add_argument('--app', type=Path, default=Path('/Applications/LibreOffice.app'))
    args = p.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        p.error('requires actual arm64 macOS; no simulated pass')
    from verify_macos_signatures import verify_oxt
    print('Final OXT signature pages:', verify_oxt(args.oxt))
    program = args.app / 'Contents/MacOS'
    print('Host platform:', platform.platform(), platform.machine(), flush=True)
    subprocess.run([str(program / 'soffice'), '--version'], check=True)
    env = dict(os.environ, PUNAKYNA_LO_MODE='local')
    for name in ('PUNAKYNA_LIBVOIKKO_PATH', 'PUNAKYNA_VOIKKO_DICTIONARY_PATH'):
        env.pop(name, None)
    # Fail closed if the old server is available: no masking by server fallback.
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 8377)) == 0:
            p.error('old server is running on 8377; stop it before this test')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='punakyna-mac-host-') as d:
        profile = Path(d) / 'profile'
        installation = '-env:UserInstallation=' + profile.as_uri()
        subprocess.run([str(program / 'unopkg'), 'add', '-f', str(args.oxt.resolve()), installation], env=env, check=True, timeout=120)
        log = open(Path(d) / 'host.log', 'w+')
        host = subprocess.Popen([str(program / 'soffice'), '--norestore', '--nologo', installation,
            '--accept=socket,host=127.0.0.1,port=%d;urp;StarOffice.ServiceManager' % port], env=env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if host.poll() is not None:
                    raise RuntimeError('LibreOffice exited before UNO was ready: %s' % host.returncode)
                with socket.socket() as probe:
                    if probe.connect_ex(('127.0.0.1', port)) == 0:
                        break
                time.sleep(.2)
            else:
                raise TimeoutError('LibreOffice UNO not ready')
            script = Path(d) / 'check.py'
            script.write_text(CHECK.replace('port=PORT;', 'port=%d;' % port))
            subprocess.run([str(args.uno_python), str(script)], env=env, check=True, timeout=120)
            if host.poll() is not None:
                raise RuntimeError('LibreOffice died during host smoke: %s' % host.returncode)
        finally:
            host.terminate()
            try:
                host.wait(timeout=10)
            except subprocess.TimeoutExpired:
                host.kill(); host.wait()
            log.seek(0)
            print(log.read())
            log.close()
    print('Host smoke passed. F7 UI, visible underline and user correction still need GUI validation.')


if __name__ == '__main__':
    main()
