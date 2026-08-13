import pytest

from core.executor import Executor
from core.vault import Vault

CONFIG = {
    "enable_repo": True,
    "repo_write": False,
    "enable_issue": True,
    "issue_write": True,
    "default_repo": "octocat/Hello-World",
    "list_limit": 10,
    "content_limit": 1500,
}


def _exec(tmp_path, config=None):
    cfg = dict(CONFIG)
    cfg.update(config or {})
    return Executor(lambda: cfg, Vault(tmp_path / "data"))


def test_executor_reads_live_config(tmp_path):
    cfg = dict(CONFIG)
    e = Executor(lambda: cfg, Vault(tmp_path / "data"))
    assert e.config["default_repo"] == "octocat/Hello-World"
    cfg["default_repo"] = "live/updated"
    assert e.config["default_repo"] == "live/updated"


def test_read_requires_group_enabled(tmp_path):
    e = _exec(tmp_path, {"enable_repo": False})
    err = e.check_permission("repo", "view", is_admin=False)
    assert err is not None and "未启用" in err


def test_write_requires_write_toggle(tmp_path):
    e = _exec(tmp_path)
    err = e.check_permission("repo", "create", is_admin=True)
    assert err is not None and "写操作" in err


def test_write_requires_admin(tmp_path):
    e = _exec(tmp_path, {"repo_write": True})
    err = e.check_permission("repo", "create", is_admin=False)
    assert err is not None and "管理员" in err


def test_write_allowed(tmp_path):
    e = _exec(tmp_path, {"repo_write": True})
    assert e.check_permission("repo", "create", is_admin=True) is None


@pytest.mark.asyncio
async def test_bot_write_allows_llm_write(tmp_path, monkeypatch):
    from core import client as client_mod

    class FakeIssue:
        number = 1
        html_url = "u"

    class FakeRepo:
        def create_issue(self, **kw):
            return FakeIssue()

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: type("G", (), {"get_repo": lambda s, n: FakeRepo()})(),
    )
    e = _exec(tmp_path, {"issue_write": True, "bot_write": True})
    result = await e.run(
        "issue",
        "create",
        {"repo": "o/r", "title": "t"},
        is_admin=False,
        sender="Alice",
        source="tool",
    )
    assert result["ok"] is True


@pytest.mark.asyncio
async def test_bot_write_off_blocks_llm_write(tmp_path):
    e = _exec(tmp_path, {"issue_write": True})
    result = await e.run(
        "issue",
        "create",
        {"repo": "o/r", "title": "t"},
        is_admin=False,
        sender="Alice",
        source="tool",
    )
    assert result["ok"] is False
    assert "管理员" in result["error"]


@pytest.mark.asyncio
async def test_bot_write_does_not_affect_command_source(tmp_path):
    e = _exec(tmp_path, {"issue_write": True, "bot_write": True})
    result = await e.run(
        "issue",
        "create",
        {"repo": "o/r", "title": "t"},
        is_admin=False,
        sender="Alice",
    )
    assert result["ok"] is False
    assert "管理员" in result["error"]


def test_read_allowed_without_admin(tmp_path):
    e = _exec(tmp_path)
    assert e.check_permission("repo", "view", is_admin=False) is None


def test_api_get_allowed_without_admin(tmp_path):
    e = _exec(tmp_path)
    err = e.check_permission(
        "api", "call", is_admin=False, params={"method": "GET"}
    )
    assert err is None


def test_api_write_requires_write_toggle(tmp_path):
    e = _exec(tmp_path)
    err = e.check_permission("api", "call", is_admin=True, params={"method": "POST"})
    assert err is not None and "写操作" in err


def test_api_write_requires_admin(tmp_path):
    e = _exec(tmp_path, {"api_write": True})
    err = e.check_permission("api", "call", is_admin=False, params={"method": "DELETE"})
    assert err is not None and "管理员" in err


def test_api_write_allowed_for_admin(tmp_path):
    e = _exec(tmp_path, {"api_write": True})
    assert (
        e.check_permission("api", "call", is_admin=True, params={"method": "PATCH"})
        is None
    )


def test_api_defaults_to_get(tmp_path):
    e = _exec(tmp_path)
    assert e.check_permission("api", "call", is_admin=False) is None


def test_unknown_group(tmp_path):
    e = _exec(tmp_path)
    assert e.check_permission("nope", "x", is_admin=False) is not None


@pytest.mark.asyncio
async def test_run_dispatches_and_wraps_error(tmp_path, monkeypatch):
    from core import client as client_mod
    from core.client import AuthError

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: (_ for _ in ()).throw(
            AuthError("尚未配置 GitHub Token，请管理员在插件配置中填写。")
        ),
    )
    e = _exec(tmp_path)
    result = await e.run(
        "repo", "view", {"repo": "octocat/Hello-World"}, user_key="tg:1", is_admin=False
    )
    assert result["ok"] is False
    assert "Token" in result["error"]


def test_handle_error_auth():
    e = _exec(__import__("pathlib").Path("/tmp/opencode/x"))
    from core.client import AuthError

    msg = e.handle_error(AuthError("尚未配置 GitHub Token，请管理员在插件配置中填写。"))
    assert "Token" in msg


def test_handle_error_unknown():
    e = _exec(__import__("pathlib").Path("/tmp/opencode/x"))
    msg = e.handle_error(ValueError("bad arg"))
    assert "bad arg" in msg


def test_long_text_action_gets_prefix(tmp_path, monkeypatch):
    from core import client as client_mod

    captured = {}

    class FakeIssue:
        number = 1
        html_url = "u"
        id = 9

    class FakeRepo:
        def create_issue(self, **kw):
            captured.update(kw)
            return FakeIssue()

    class FakeGh:
        def get_repo(self, name):
            return FakeRepo()

    monkeypatch.setattr(client_mod.GhClient, "get_github", lambda self: FakeGh())
    e = _exec(tmp_path, {"text_prefix": "🤖 bot {sender}", "issue_write": True})
    result = __import__("asyncio").run(
        e.run(
            "issue",
            "create",
            {"repo": "o/r", "title": "t", "body": "hello"},
            is_admin=True,
            sender="Alice",
        )
    )
    assert result["ok"] is True
    assert captured["body"].startswith("🤖 bot Alice\n\nhello")


def test_long_text_action_no_prefix_when_unset(tmp_path, monkeypatch):
    from core import client as client_mod

    captured = {}

    class FakeIssue:
        number = 1
        html_url = "u"

    class FakeRepo:
        def create_issue(self, **kw):
            captured.update(kw)
            return FakeIssue()

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: type("G", (), {"get_repo": lambda s, n: FakeRepo()})(),
    )
    e = _exec(tmp_path, {"issue_write": True})
    result = __import__("asyncio").run(
        e.run(
            "issue",
            "create",
            {"repo": "o/r", "title": "t", "body": "hello"},
            is_admin=True,
            sender="Alice",
        )
    )
    assert result["ok"] is True
    assert captured["body"] == "hello"


def test_non_long_text_action_untouched(tmp_path, monkeypatch):
    from core import client as client_mod

    captured = {}

    class FakeUser:
        def create_repo(self, name, **kw):
            captured.update(kw)
            return type("R", (), {"full_name": "n", "html_url": "u"})()

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: type("G", (), {"get_user": lambda s: FakeUser()})(),
    )
    e = _exec(tmp_path, {"repo_write": True, "text_prefix": "🤖 bot"})
    result = __import__("asyncio").run(
        e.run(
            "repo",
            "create",
            {"name": "n", "description": "hello"},
            is_admin=True,
            sender="Alice",
        )
    )
    assert result["ok"] is True
    assert captured["description"] == "hello"


def test_audit_recorded_on_success(tmp_path, monkeypatch):
    from core import client as client_mod
    from core.audit import AuditLog

    class FakeIssue:
        number = 1
        html_url = "u"

    class FakeRepo:
        def create_issue(self, **kw):
            return FakeIssue()

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: type("G", (), {"get_repo": lambda s, n: FakeRepo()})(),
    )
    audit = AuditLog(tmp_path / "audit")
    e = _exec(tmp_path, {"issue_write": True, "audit_enabled": True})
    e.audit = audit
    result = __import__("asyncio").run(
        e.run(
            "issue",
            "create",
            {"repo": "o/r", "title": "t", "body": "hello"},
            is_admin=True,
            sender="Alice",
            umo="telegram:private:12345",
        )
    )
    assert result["ok"] is True
    entries = audit.list_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["sender"] == "Alice"
    assert entry["umo"] == "telegram:private:12345"
    assert entry["group"] == "issue"
    assert entry["action"] == "create"
    assert entry["source"] == "command"
    assert entry["ok"] is True
    assert entry["body_preview"] == "hello"
    assert "default_repo" not in entry["params"]
    assert "error" not in entry


def test_run_injects_default_repo_for_tool_source(tmp_path, monkeypatch):
    from core import client as client_mod
    from core.audit import AuditLog

    captured = {}

    class FakeIssue:
        number = 1
        html_url = "u"

    def fake_get_repo(self, name):
        captured["name"] = name
        return type("R", (), {"create_issue": lambda s, **kw: FakeIssue()})()

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: type("G", (), {"get_repo": fake_get_repo})(),
    )
    audit = AuditLog(tmp_path / "audit")
    e = _exec(tmp_path, {"issue_write": True, "bot_write": True, "audit_enabled": True})
    e.audit = audit
    result = __import__("asyncio").run(
        e.run(
            "issue",
            "create",
            {"title": "t"},
            is_admin=False,
            sender="Alice",
            source="tool",
            umo="tg:1",
        )
    )
    assert result["ok"] is True
    assert captured["name"] == "octocat/Hello-World"
    entries = audit.list_entries()
    assert entries[0]["repo"] == "octocat/Hello-World"
    assert entries[0]["source"] == "tool"


def test_audit_recorded_on_failure(tmp_path, monkeypatch):
    from core import client as client_mod
    from core.audit import AuditLog
    from core.client import AuthError

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: (_ for _ in ()).throw(
            AuthError("尚未配置 GitHub Token，请管理员在插件配置中填写。")
        ),
    )
    audit = AuditLog(tmp_path / "audit")
    e = _exec(tmp_path, {"audit_enabled": True})
    e.audit = audit
    result = __import__("asyncio").run(
        e.run("repo", "view", {"repo": "o/r"}, user_key="tg:1", sender="Bob")
    )
    assert result["ok"] is False
    entries = audit.list_entries()
    assert len(entries) == 1
    assert entries[0]["ok"] is False
    assert "Token" in entries[0]["error"]


def test_audit_skipped_when_disabled(tmp_path, monkeypatch):
    from core import client as client_mod
    from core.audit import AuditLog

    class FakeIssue:
        number = 1
        html_url = "u"

    monkeypatch.setattr(
        client_mod.GhClient,
        "get_github",
        lambda self: type(
            "G",
            (),
            {
                "get_repo": lambda s, n: type(
                    "R", (), {"create_issue": lambda self, **kw: FakeIssue()}
                )()
            },
        )(),
    )
    audit = AuditLog(tmp_path / "audit")
    e = _exec(tmp_path, {"issue_write": True, "audit_enabled": False})
    e.audit = audit
    __import__("asyncio").run(
        e.run(
            "issue",
            "create",
            {"repo": "o/r", "title": "t"},
            is_admin=True,
            sender="Alice",
        )
    )
    assert audit.list_entries() == []


def test_audit_skipped_when_not_configured(tmp_path):

    e = _exec(tmp_path, {"issue_write": True})
    assert e.audit is None
    result = __import__("asyncio").run(
        e.run(
            "issue",
            "create",
            {"repo": "o/r", "title": "t"},
            is_admin=True,
            sender="Alice",
        )
    )
    assert result["ok"] is False  # no real token — but must not crash on audit
