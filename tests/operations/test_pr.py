from types import SimpleNamespace

from core.operations import pr


def _pr(number, title, state, head="feat", base="main", merged=False):
    return SimpleNamespace(
        number=number,
        title=title,
        state=state,
        body="",
        html_url="u",
        head=SimpleNamespace(ref=head),
        base=SimpleNamespace(ref=base),
        merged=merged,
        user=SimpleNamespace(login="alice"),
        created_at=None,
    )


def _client(repo):
    class Fake:
        def get_repo(self, name):
            return repo

    return SimpleNamespace(get_github=lambda: Fake())


def test_list():
    repo = SimpleNamespace(
        get_pulls=lambda state="open": [_pr(1, "a", "open"), _pr(2, "b", "closed")]
    )
    data = pr.HANDLERS["list"](_client(repo), {"repo": "o/r", "state": "open"})
    assert len(data) == 2


def test_merge():
    p = _pr(1, "a", "open")
    calls = {"merged": False}
    p.merge = lambda **kw: calls.update(merged=True)
    repo = SimpleNamespace(get_pull=lambda n: p)
    data = pr.HANDLERS["merge"](_client(repo), {"repo": "o/r", "number": 1})
    assert data["ok"] is True
    assert calls["merged"] is True


def test_write_metadata():
    assert "merge" in pr.WRITE
    assert "review" in pr.WRITE
    assert "edit" in pr.WRITE
    assert "delete" not in pr.WRITE


def test_edit():
    calls = {}

    def fake_edit(**kwargs):
        calls.update(kwargs)

    p = _pr(1, "a", "open")
    p.edit = fake_edit
    repo = SimpleNamespace(get_pull=lambda n: p)
    data = pr.HANDLERS["edit"](
        _client(repo),
        {"repo": "o/r", "number": 1, "title": "新标题", "labels": "bug, feat"},
    )
    assert data["ok"] is True
    assert calls["title"] == "新标题"
    assert calls["labels"] == ["bug", "feat"]


def test_format_list():
    out = pr.format([{"number": 1, "title": "a", "state": "open"}], 10, 1500)
    assert "#1" in out
