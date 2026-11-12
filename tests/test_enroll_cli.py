"""Enrollment-CLI: rekisteröinti, listaus, peruutus."""


def test_enroll_list_revoke(tmp_path, monkeypatch):
    import punakyna.tokenfile as tf
    monkeypatch.setattr(tf, 'TOKENS_DIR', tmp_path / 'tokens')
    monkeypatch.setattr(tf, 'TOKEN_PATH', tmp_path / 'token')
    from punakyna.cli import main
    assert main(['--enroll-app', 'testisov']) == 0
    assert (tmp_path / 'tokens' / 'testisov').exists()
    assert main(['--list-apps']) == 0
    assert main(['--revoke-app', 'testisov']) == 0
    assert not (tmp_path / 'tokens' / 'testisov').exists()
    assert main(['--revoke-app', 'testisov']) == 1
