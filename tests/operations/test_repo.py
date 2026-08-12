from types import SimpleNamespace

from core.client import GhClient
from core.operations import repo


def _gh(attrs: dict) -> SimpleNamespace:
    return SimpleNamespace(**attrs)


def _client(g: SimpleNamespace, token="ghp_t") -> GhClient:
    class Fake:
        def get_repo(self, full_name):
            assert full_name == "octocat/Hello-World"
            return g

        def get_user(self, login=None):
            return g

    c = GhClient.__new__(GhClient)
    c.user_key = None
    c.resolve_token = lambda: token
    c.get_github = lambda: Fake()
    return c


def test_view():
    g = _gh(
        {
            "full_name": "octocat/Hello-World",
            "description": "hello",
            "html_url": "https://github.com/octocat/Hello-World",
            "stargazers_count": 5,
            "forks_count": 2,
            "open_issues_count": 1,
            "language": "Python",
            "default_branch": "main",
            "private": False,
        }
    )
    data = repo.HANDLERS["view"](_client(g), {"repo": "octocat/Hello-World"})
    assert data["full_name"] == "octocat/Hello-World"
    assert data["stargazers_count"] == 5


def test_list_repos():
    r1 = SimpleNamespace(
        full_name="a/b",
        description=None,
        stargazers_count=0,
        language="Python",
        private=False,
    )
    r2 = SimpleNamespace(
        full_name="c/d",
        description="d",
        stargazers_count=9,
        language="Go",
        private=True,
    )
    u = _gh({"get_repos": lambda: [r1, r2]})
    data = repo.HANDLERS["list"](_client(u), {})
    assert len(data) == 2
    assert data[0]["full_name"] == "a/b"


def test_star_format():
    out = repo.format({"ok": True, "starred": "o/r"}, 10, 1500)
    assert "o/r" in out


def test_create_requires_write_flag_metadata():
    assert "create" in repo.WRITE


def test_format_limit():
    out = repo.format(
        [
            {"full_name": f"o/r{i}", "description": None, "stargazers_count": 0}
            for i in range(20)
        ],
        list_limit=10,
        content_limit=1500,
    )
    assert out.count("o/r") == 10
    assert "已截断" in out
