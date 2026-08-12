import pytest

from core.operations import run


class _FakeClient:
    def __init__(self, responses):
        self._responses = responses

    async def rest(self, method, path, params=None, body=None):
        return self._responses[path]


@pytest.mark.asyncio
async def test_runs_ok():
    c = _FakeClient(
        {
            "/repos/o/r/actions/runs": (
                200,
                {
                    "total_count": 1,
                    "workflow_runs": [
                        {
                            "id": 1,
                            "name": "ci",
                            "status": "completed",
                            "conclusion": "success",
                            "head_branch": "main",
                            "html_url": "u/1",
                            "run_number": 5,
                        }
                    ],
                },
            )
        }
    )
    data = await run.HANDLERS["runs"](c, {"repo": "o/r"})
    assert data["total"] == 1
    assert data["runs"][0]["conclusion"] == "success"


def test_run_dispatch_write():
    assert "run" in run.WRITE


@pytest.mark.asyncio
async def test_registry_dispatches_async(monkeypatch):
    from core.operations import registry
    from core.operations import run as run_mod

    c = _FakeClient(
        {"/repos/o/r/actions/runs": (200, {"total_count": 0, "workflow_runs": []})}
    )
    monkeypatch.setattr(registry, "_GROUPS", {"run": run_mod})
    data = await registry.run(c, "run", "runs", {"repo": "o/r"})
    assert data["total"] == 0
