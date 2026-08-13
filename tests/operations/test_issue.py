from types import SimpleNamespace

import pytest

from core.operations import issue


def _issue(number, title, state, labels=(), body="", html_url="u"):
    return SimpleNamespace(
        number=number,
        title=title,
        state=state,
        body=body,
        html_url=html_url,
        labels=[SimpleNamespace(name=l) for l in labels],
        user=SimpleNamespace(login="alice"),
        created_at=None,
    )


def _client(repo):
    class Fake:
        def get_repo(self, name):
            return repo

        def get_issue(self, name, number):
            return repo.get_issue(number)

    c = SimpleNamespace(
        get_github=lambda: Fake(),
        user_key=None,
        resolve_token=lambda: "t",
    )
    return c


def test_list():
    repo = SimpleNamespace(
        get_issues=lambda state="open": [
            _issue(1, "a", "open"),
            _issue(2, "b", "closed"),
        ]
    )
    data = issue.HANDLERS["list"](_client(repo), {"repo": "o/r", "state": "open"})
    assert len(data) == 2
    assert data[0]["number"] == 1


def test_view():
    repo = SimpleNamespace(get_issue=lambda n: _issue(42, "hi", "open"))
    data = issue.HANDLERS["view"](_client(repo), {"repo": "o/r", "number": 42})
    assert data["title"] == "hi"


def test_write_metadata():
    assert "close" in issue.WRITE
    assert "comment" in issue.WRITE
    assert "edit" in issue.WRITE
    assert "delete" not in issue.WRITE


def test_edit_labels():
    calls = {}

    def fake_edit(**kwargs):
        calls.update(kwargs)

    repo = SimpleNamespace(
        get_issue=lambda n: SimpleNamespace(
            number=n, html_url="u", edit=fake_edit, state="open", title="t", labels=[]
        )
    )
    data = issue.HANDLERS["edit"](
        _client(repo), {"repo": "o/r", "number": 42, "labels": "bug, help wanted"}
    )
    assert data["ok"] is True
    assert calls["labels"] == ["bug", "help wanted"]


def test_edit_multiple_fields():
    calls = {}

    def fake_edit(**kwargs):
        calls.update(kwargs)

    repo = SimpleNamespace(
        get_issue=lambda n: SimpleNamespace(number=n, html_url="u", edit=fake_edit)
    )
    issue.HANDLERS["edit"](
        _client(repo),
        {"repo": "o/r", "number": 1, "title": "新标题", "body": "新正文"},
    )
    assert calls["title"] == "新标题"
    assert calls["body"] == "新正文"


def test_edit_requires_change():
    repo = SimpleNamespace(
        get_issue=lambda n: SimpleNamespace(number=n, html_url="u", edit=lambda **k: None)
    )
    with pytest.raises(ValueError):
        issue.HANDLERS["edit"](_client(repo), {"repo": "o/r", "number": 1})


def test_format():
    out = issue.format([{"number": 1, "title": "a", "state": "open"}], 10, 1500)
    assert "#1" in out and "a" in out
