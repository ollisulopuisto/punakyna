"""Rekisterin eheys: jokainen emittoitu sääntö-id on rekisterissä, lähteellinen
ja testattu; kattavuuskartta on ajan tasalla."""
import pathlib
import re
import subprocess
import sys

from punakyna.registry import REGISTRY

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _emitted_ids():
    ids = set()
    for p in (ROOT / 'punakyna').glob('*.py'):
        text = p.read_text()
        ids |= set(re.findall(r"rule='([A-Z_]+)'", text))
        ids |= set(re.findall(r"Suggestion\('([A-Z_]+)'", text))
    return ids


def test_every_emitted_rule_is_registered():
    assert _emitted_ids() <= {r.id for r in REGISTRY}


def test_no_registered_rule_is_dead():
    assert {r.id for r in REGISTRY} <= _emitted_ids()


def test_ids_unique_and_sourced():
    ids = [r.id for r in REGISTRY]
    assert len(ids) == len(set(ids))
    for r in REGISTRY:
        assert r.sources and all(s.startswith('https://') for s in r.sources), r.id
        assert r.source_status in ('verified', 'chapter', 'engine'), r.id
        assert r.severity in ('error', 'warning', 'style', 'info'), r.id


def test_test_modules_exist():
    for r in REGISTRY:
        for t in r.tests:
            assert (ROOT / 'tests' / t).exists(), (r.id, t)


def test_coverage_map_up_to_date():
    rc = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'gen_coverage_map.py'),
                         '--check']).returncode
    assert rc == 0, 'run: python scripts/gen_coverage_map.py'
