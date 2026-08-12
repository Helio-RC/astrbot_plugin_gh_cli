from types import SimpleNamespace

from core.operations import search


def _client(repo):
    class Fake:
        def search_repositories(self, q, **kw):
            return [
                SimpleNamespace(full_name=f"r{i}", description=None, stargazers_count=1)
                for i in range(2)
            ]

        def search_issues(self, q, **kw):
            return [SimpleNamespace(number=1, title="t", state="open", html_url="u")]

    return SimpleNamespace(get_github=lambda: Fake())


def test_repos():
    data = search.HANDLERS["repos"](_client(None), {"query": "astrbot"})
    assert len(data) == 2


def test_no_write():
    assert search.WRITE == set()


def test_format():
    out = search.format(
        [{"full_name": "a/b", "description": None, "stargazers_count": 1}], 10, 1500
    )
    assert "a/b" in out
