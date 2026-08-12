from core.config_ingest import ingest_tokens, normalize_default_repo
from core.vault import Vault


def test_normalize_repo_url():
    assert (
        normalize_default_repo("https://github.com/Helio-RC/astrbot_plugin_gh_cli")
        == "Helio-RC/astrbot_plugin_gh_cli"
    )


def test_normalize_repo_url_with_git_and_path():
    assert normalize_default_repo("https://github.com/o/r.git") == "o/r"
    assert normalize_default_repo("https://github.com/o/r/tree/main") == "o/r"


def test_normalize_repo_bare_and_trailing_slash():
    assert (
        normalize_default_repo("Helio-RC/astrbot_plugin_gh_cli")
        == "Helio-RC/astrbot_plugin_gh_cli"
    )
    assert normalize_default_repo("o/r/") == "o/r"
    assert normalize_default_repo("  ") == ""


def test_normalize_repo_www_and_schemaless():
    assert normalize_default_repo("www.github.com/o/r") == "o/r"
    assert normalize_default_repo("github.com/o/r") == "o/r"


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
