import pytest

from core.operations import api


class _FakeClient:
    def __init__(self, responses):
        self._responses = responses
        self.last = None

    async def rest(self, method, path, params=None, body=None):
        self.last = (method, path, params, body)
        return self._responses[path]


@pytest.mark.asyncio
async def test_get():
    c = _FakeClient({"/repos/o/r": (200, {"full_name": "o/r"})})
    data = await api.HANDLERS["call"](c, {"method": "GET", "path": "/repos/o/r"})
    assert data["status"] == 200
    assert data["data"]["full_name"] == "o/r"


def test_write_set():
    assert "DELETE" in api.WRITE
    assert "GET" not in api.WRITE


def test_format_error():
    out = api.format(
        {"status": 404, "data": {"message": "Not Found"}, "ok": False}, 10, 1500
    )
    assert "404" in out
