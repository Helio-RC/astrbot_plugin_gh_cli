from types import SimpleNamespace

from core.operations import gist


def _gist(gid, description, files=None):
    return SimpleNamespace(
        id=gid,
        description=description or "",
        html_url=f"u/{gid}",
        files={
            k: SimpleNamespace(filename=k, content=v) for k, v in (files or {}).items()
        },
        created_at=None,
    )


def _client(g):
    class Fake:
        def get_gist(self, gid):
            return g

    return SimpleNamespace(get_github=lambda: Fake())


def test_create():
    created = {}

    class FakeUser:
        def create_gist(self, public, files, description=""):
            created.update(
                {"public": public, "files": files, "description": description}
            )
            return _gist("abc", description, files)

    class FakeGh:
        def get_user(self):
            return FakeUser()

    c = SimpleNamespace(get_github=lambda: FakeGh())
    data = gist.HANDLERS["create"](
        c, {"description": "demo", "files": {"a.txt": "hello"}, "public": False}
    )
    assert data["ok"] is True
    assert created["files"]["a.txt"]._identity == {"content": "hello"}


def test_view():
    g = _gist("abc", "desc", {"a.txt": "hi"})
    data = gist.HANDLERS["view"](_client(g), {"id": "abc"})
    assert data["files"]["a.txt"] == "hi"


def test_write_metadata():
    assert "delete" in gist.WRITE
    assert "edit" in gist.WRITE
    assert "comment" in gist.WRITE


def test_edit():
    g = _gist("abc", "desc", {"a.txt": "hi"})
    calls = {}
    g.edit = lambda **kw: calls.update(kw)
    data = gist.HANDLERS["edit"](
        _client(g),
        {"id": "abc", "description": "新描述", "files": {"a.txt": "hello", "b.txt": "x"}},
    )
    assert data["ok"] is True
    assert calls["description"] == "新描述"
    assert calls["files"]["a.txt"]._identity == {"content": "hello"}
    assert calls["files"]["b.txt"]._identity == {"content": "x"}


def test_comment():
    g = _gist("abc", "desc")
    calls = {}
    g.create_comment = lambda body: calls.update(body=body) or SimpleNamespace(id=7)
    data = gist.HANDLERS["comment"](_client(g), {"id": "abc", "body": "很好"})
    assert data["ok"] is True
    assert calls["body"] == "很好"


def test_format():
    out = gist.format(
        {"id": "abc", "description": "d", "files": {"a.txt": "hi"}}, 10, 1500
    )
    assert "abc" in out
