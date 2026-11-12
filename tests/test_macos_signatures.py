"""Cross-platform signature-page regression tests, not Mac host validation."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('signatures', ROOT / 'adapters/libreoffice/xproofreader/verify_macos_signatures.py')
SIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIG)


def signed_fixture():
    code = bytearray(4096)
    struct.pack_into('<8I', code, 0, 0xfeedfacf, 0x100000c, 0, 6, 1, 16, 0, 0)
    struct.pack_into('<4I', code, 32, 0x1d, 16, 4096, 108)
    cd = bytearray(88)
    struct.pack_into('>9I', cd, 0, 0xfade0c02, 88, 0x20400, 2, 56, 44, 0, 1, 4096)
    struct.pack_into('>4B', cd, 36, 32, 2, 0, 12)
    cd[44:49] = b'test\0'
    cd[56:88] = hashlib.sha256(code).digest()
    return bytes(code) + struct.pack('>5I', 0xfade0cc0, 108, 1, 0, 20) + cd


def test_valid_page_hash():
    assert SIG.verify_bytes(signed_fixture()) == 1


def test_relink_after_signing_rejected():
    data = bytearray(signed_fixture())
    data[60] ^= 1
    with pytest.raises(ValueError, match='page 0 does not match'):
        SIG.verify_bytes(data)


def test_missing_signature_rejected():
    data = bytearray(signed_fixture())
    struct.pack_into('<I', data, 16, 0)
    with pytest.raises(ValueError, match='missing embedded'):
        SIG.verify_bytes(data)


def test_signing_happens_after_fixups_and_before_packing():
    source = (ROOT / 'adapters/libreoffice/xproofreader/bundle_native.py').read_text()
    main = source[source.index('def main():'):]
    assert main.index('_macos_fixups(libdir)') < main.index('_macos_verify(libdir)') < main.index('_macos_sign_and_verify(libdir)')
    workflow = (ROOT / '.github/workflows/build-full-oxt.yml').read_text()
    assert workflow.index('verify_macos_signatures.py dist/') < workflow.index('gh release create')
    assert '  push:' not in workflow


def test_all_final_libraries_are_signed_then_verified(tmp_path, monkeypatch):
    path = ROOT / 'adapters/libreoffice/xproofreader'
    monkeypatch.syspath_prepend(str(path))
    import bundle_native
    import verify_macos_signatures
    calls = []
    monkeypatch.setattr(bundle_native.subprocess, 'run', lambda cmd, **kw: calls.append(cmd))
    checked = []
    monkeypatch.setattr(verify_macos_signatures, 'verify_bytes', lambda data: checked.append(data))
    (tmp_path / 'a.dylib').write_bytes(b'final-a')
    (tmp_path / 'b.dylib').write_bytes(b'final-b')
    bundle_native._macos_sign_and_verify(str(tmp_path))
    assert [c[1] for c in calls] == ['--force', '--force', '--verify', '--verify']
    assert checked == [b'final-a', b'final-b']


def test_failed_signing_stops_packaging(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.syspath_prepend(str(ROOT / 'adapters/libreoffice/xproofreader'))
    import bundle_native
    (tmp_path / 'a.dylib').write_bytes(b'final')
    def fail(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(bundle_native.subprocess, 'run', fail)
    with pytest.raises(subprocess.CalledProcessError):
        bundle_native._macos_sign_and_verify(str(tmp_path))


def test_zero_actions_storage_workflow():
    workflow = (ROOT / '.github/workflows/build-full-oxt.yml').read_text()
    assert 'runs-on: macos-15' in workflow
    assert 'actions/upload-artifact' not in workflow
    assert 'actions/cache' not in workflow
    assert '--draft --prerelease' in workflow
    assert workflow.index('test_macos_host.py') < workflow.index('gh release create')
