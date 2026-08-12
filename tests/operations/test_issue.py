from types import SimpleNamespace

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


def test_format():
    out = issue.format([{"number": 1, "title": "a", "state": "open"}], 10, 1500)
    assert "#1" in out and "a" in out
