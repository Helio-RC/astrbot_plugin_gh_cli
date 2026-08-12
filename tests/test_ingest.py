from core.config_ingest import ingest_tokens
from core.vault import Vault


def test_ingest_shared(tmp_path):
    vault = Vault(tmp_path / "d")
    changes = ingest_tokens({"shared_token": "ghp_abc"}, vault)
    assert changes["shared_token"] == ""
    assert vault.get_shared_token() == "ghp_abc"


def test_ingest_skips_empty(tmp_path):
    vault = Vault(tmp_path / "d")
    changes = ingest_tokens({"shared_token": ""}, vault)
    assert changes == {}
    assert vault.get_shared_token() is None


def test_ingest_personal(tmp_path):
    vault = Vault(tmp_path / "d")
    cfg = {
        "personal_tokens": [
            {"__template_key": "t1", "name": "alice", "token": "ghp_alice"},
            {"__template_key": "t1", "name": "bob", "token": ""},
        ]
    }
    changes = ingest_tokens(cfg, vault)
    assert vault.get_personal_token("alice") == "ghp_alice"
    assert vault.get_personal_token("bob") is None
    assert changes["personal_tokens"][0]["token"] == ""
    assert changes["personal_tokens"][1]["token"] == ""
