import json
from pathlib import Path

from core.vault import Vault


def _make_vault(tmp_path: Path) -> Vault:
    return Vault(tmp_path / "data")


def test_shared_token_roundtrip(tmp_path):
    v = _make_vault(tmp_path)
    v.set_shared_token("ghp_123")
    v2 = _make_vault(tmp_path)
    assert v2.get_shared_token() == "ghp_123"


def test_personal_token_roundtrip(tmp_path):
    v = _make_vault(tmp_path)
    v.set_personal_token("alice", "ghp_alice")
    v2 = _make_vault(tmp_path)
    assert v2.get_personal_token("alice") == "ghp_alice"
    assert v2.list_personal_token_names() == ["alice"]


def test_remove_personal_token(tmp_path):
    v = _make_vault(tmp_path)
    v.set_personal_token("alice", "ghp_alice")
    v.remove_personal_token("alice")
    assert v.get_personal_token("alice") is None


def test_binding_roundtrip(tmp_path):
    v = _make_vault(tmp_path)
    v.set_binding("telegram:private:1", "alice")
    v2 = _make_vault(tmp_path)
    assert v2.get_binding("telegram:private:1") == "alice"
    v2.remove_binding("telegram:private:1")
    assert v2.get_binding("telegram:private:1") is None


def test_secrets_file_is_encrypted(tmp_path):
    import pytest

    v = _make_vault(tmp_path)
    v.set_shared_token("ghp_123")
    raw = (tmp_path / "data" / "secrets.json").read_text()
    assert "ghp_123" not in raw
    assert raw != "ghp_123"
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)  # stored form is an encrypted Fernet token, not plain JSON


def test_secrets_file_permissions(tmp_path):
    v = _make_vault(tmp_path)
    v.set_shared_token("ghp_123")
    mode = (tmp_path / "data" / "secrets.json").stat().st_mode & 0o777
    assert mode == 0o600


def test_master_key_file_permissions(tmp_path):
    _make_vault(tmp_path)
    mode = (tmp_path / "data" / "master.key").stat().st_mode & 0o777
    assert mode == 0o600


def test_no_data_dir_creates_one(tmp_path):
    _make_vault(tmp_path)
    assert (tmp_path / "data").is_dir()


def test_refuses_overwrite_after_decrypt_failure(tmp_path):
    import pytest

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "secrets.json").write_text("garbage-not-a-valid-fernet-token")
    v = Vault(data_dir)
    with pytest.raises(RuntimeError):
        v.set_shared_token("ghp_should_not_persist")
