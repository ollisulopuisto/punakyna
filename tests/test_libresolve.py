"""Kirjastopolun selvitys (macOS-dylib-regressio, ilman Macia)."""
import os

from punakyna.voikko_gc import _resolve_libfile, _CANDIDATES


def test_directory_prefers_existing_candidate(tmp_path):
    (tmp_path / 'libvoikko.1.dylib').write_bytes(b'')
    assert _resolve_libfile(str(tmp_path)) == \
        str(tmp_path / 'libvoikko.1.dylib')


def test_directory_linux_order(tmp_path):
    (tmp_path / 'libvoikko.so.1').write_bytes(b'')
    (tmp_path / 'libvoikko.1.dylib').write_bytes(b'')
    assert _resolve_libfile(str(tmp_path)) == str(tmp_path / 'libvoikko.so.1')


def test_direct_file_override(tmp_path):
    f = tmp_path / 'custom-name.dylib'
    f.write_bytes(b'')
    assert _resolve_libfile(str(f)) == str(f)


def test_missing_dir_returns_first_candidate(tmp_path):
    out = _resolve_libfile(str(tmp_path))
    assert out == os.path.join(str(tmp_path), _CANDIDATES[0])
