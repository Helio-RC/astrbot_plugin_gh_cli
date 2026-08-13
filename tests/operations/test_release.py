from types import SimpleNamespace

from core.operations import release


def _rel(tag, name, draft=False, prerelease=False, body=""):
    return SimpleNamespace(
        tag_name=tag,
        name=name,
        draft=draft,
        prerelease=prerelease,
        body=body,
        html_url=f"u/{tag}",
        created_at=None,
        assets=[],
    )


def _client(repo):
    class Fake:
        def get_repo(self, name):
            return repo

    return SimpleNamespace(get_github=lambda: Fake())


def test_list():
    repo = SimpleNamespace(get_releases=lambda: [_rel("v1", "v1"), _rel("v2", "v2")])
    data = release.HANDLERS["list"](_client(repo), {"repo": "o/r"})
    assert len(data) == 2
    assert data[0]["tag"] == "v1"


def test_delete():
    r = _rel("v1", "v1")
    deleted = {"d": False}
    r.delete_release = lambda: deleted.update(d=True)
    repo = SimpleNamespace(get_release=lambda tag: r)
    data = release.HANDLERS["delete"](_client(repo), {"repo": "o/r", "tag": "v1"})
    assert data["ok"] is True
    assert deleted["d"] is True


def test_write_metadata():
    assert "delete" in release.WRITE
    assert "edit" in release.WRITE


def test_edit():
    r = _rel("v1", "v1")
    calls = {}
    r.update_release = lambda **kw: calls.update(kw)
    repo = SimpleNamespace(get_release=lambda tag: r)
    data = release.HANDLERS["edit"](
        _client(repo),
        {"repo": "o/r", "tag": "v1", "name": "v2", "body": "新说明", "prerelease": True},
    )
    assert data["ok"] is True
    assert calls == {"name": "v2", "message": "新说明", "prerelease": True}


def test_format():
    out = release.format(
        [{"tag": "v1", "name": "v1", "draft": False, "prerelease": False}], 10, 1500
    )
    assert "v1" in out
