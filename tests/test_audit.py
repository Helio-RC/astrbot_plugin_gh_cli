"""Tests for the audit log feature."""

import json
from pathlib import Path

from core.audit import AuditLog

AUDIT_FILE = "audit.jsonl"


def _make(tmp_path: Path, limit: int = 1000) -> AuditLog:
    return AuditLog(tmp_path / "data", limit=limit)


def _entry(i: int, sender="alice", group="repo", ok=True, **kw):
    entry = {
        "ts": f"2026-08-12T00:00:{i:02d}",
        "sender": sender,
        "source": "command",
        "group": group,
        "action": "view",
        "repo": "o/r",
        "params": ["repo"],
        "body_preview": "",
        "ok": ok,
        **kw,
    }
    return entry


def test_record_creates_file(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1))
    assert (tmp_path / "data" / AUDIT_FILE).exists()


def test_record_creates_dir(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1))
    assert (tmp_path / "data").is_dir()


def test_file_permissions(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1))
    mode = (tmp_path / "data" / AUDIT_FILE).stat().st_mode & 0o777
    assert mode == 0o600


def test_list_newest_first(tmp_path):
    log = _make(tmp_path)
    for i in range(3):
        log.record(_entry(i))
    entries = log.list_entries()
    assert [e["action"] for e in entries] == ["view", "view", "view"]
    assert entries[0]["ts"] == "2026-08-12T00:00:02"


def test_list_limit(tmp_path):
    log = _make(tmp_path)
    for i in range(5):
        log.record(_entry(i))
    assert len(log.list_entries(limit=2)) == 2
    assert len(log.list_entries()) == 5


def test_filter_by_sender(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1, sender="alice"))
    log.record(_entry(2, sender="bob"))
    assert len(log.list_entries(sender="alice")) == 1
    assert log.list_entries(sender="alice")[0]["sender"] == "alice"


def test_filter_by_group(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1, group="repo"))
    log.record(_entry(2, group="issue"))
    assert len(log.list_entries(group="issue")) == 1


def test_filter_by_ok(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1, ok=True))
    log.record(_entry(2, ok=False))
    assert len(log.list_entries(ok=True)) == 1
    assert len(log.list_entries(ok=False)) == 1


def test_limit_rollover_keeps_newest(tmp_path):
    log = _make(tmp_path, limit=3)
    for i in range(6):
        log.record(_entry(i))
    entries = log.list_entries()
    assert len(entries) == 3
    assert entries[0]["ts"] == "2026-08-12T00:00:05"
    assert entries[-1]["ts"] == "2026-08-12T00:00:03"


def test_clear(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1))
    log.clear()
    assert log.list_entries() == []
    assert log.stats()["total"] == 0


def test_stats(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1, ok=True))
    log.record(_entry(2, ok=False))
    stats = log.stats()
    assert stats["total"] == 2
    assert stats["ok_count"] == 1
    assert stats["fail_count"] == 1
    assert stats["last_ts"] == "2026-08-12T00:00:02"


def test_stats_empty(tmp_path):
    log = _make(tmp_path)
    stats = log.stats()
    assert stats["total"] == 0
    assert stats["ok_count"] == 0
    assert stats["fail_count"] == 0
    assert stats["last_ts"] is None


def test_record_invalid_entry_does_not_crash(tmp_path):
    log = _make(tmp_path)
    log.record({"ts": "x"})  # missing fields — should not raise
    assert len(log.list_entries()) == 1


def test_body_preview_truncation(tmp_path):
    log = _make(tmp_path)
    entry = _entry(1)
    entry["body_preview"] = "x" * 500
    log.record(entry)
    assert len(log.list_entries()[0]["body_preview"]) == 100


def test_error_truncation(tmp_path):
    log = _make(tmp_path)
    entry = _entry(1, ok=False, error="e" * 500)
    log.record(entry)
    assert len(log.list_entries()[0]["error"]) == 200


def test_records_are_valid_jsonl(tmp_path):
    log = _make(tmp_path)
    log.record(_entry(1))
    log.record(_entry(2, sender="bob", group="pr", ok=False, error="boom"))
    raw = (tmp_path / "data" / AUDIT_FILE).read_text().strip().splitlines()
    assert len(raw) == 2
    for line in raw:
        obj = json.loads(line)
        assert "ts" in obj and "sender" in obj and "ok" in obj
