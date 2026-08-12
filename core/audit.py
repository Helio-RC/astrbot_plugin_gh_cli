"""Audit log: JSONL record of plugin GitHub operations."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIT_FILE = "audit.jsonl"
BODY_PREVIEW_LEN = 100
ERROR_LEN = 200
DEFAULT_LIMIT = 1000


class AuditLog:
    """Append-only JSONL audit store with a rolling size cap.

    Entries are dicts with at least: ts, sender, source, group, action,
    repo, params, body_preview, ok (and optionally error). Storage failures
    degrade to a warning log — auditing must never break the caller.
    """

    def __init__(self, data_dir: Path, limit: int = DEFAULT_LIMIT) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.limit = max(1, int(limit))
        self._path = self.data_dir / AUDIT_FILE

    def _ensure_file(self) -> None:
        if not self._path.exists():
            self._path.touch(mode=0o600, exist_ok=True)

    def record(self, entry: dict) -> None:
        # Defensive truncation: callers may pass arbitrarily long values.
        if isinstance(entry.get("body_preview"), str):
            entry["body_preview"] = entry["body_preview"][:BODY_PREVIEW_LEN]
        if isinstance(entry.get("error"), str):
            entry["error"] = entry["error"][:ERROR_LEN]
        try:
            self._ensure_file()
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._trim_if_needed()
        except OSError as exc:
            logger.warning("审计日志写入失败: %s", exc)

    def _trim_if_needed(self) -> None:
        if self.limit <= 0:
            return
        try:
            count = sum(1 for _ in self._path.open("r", encoding="utf-8"))
        except OSError:
            return
        if count <= self.limit:
            return
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
            keep = lines[-self.limit :]
            self._path.write_text("\n".join(keep) + "\n", encoding="utf-8")
        except OSError as exc:
            logger.warning("审计日志裁剪失败: %s", exc)

    def list_entries(
        self,
        sender: str = "",
        group: str = "",
        ok: bool | None = None,
        limit: int = 200,
    ) -> list[dict]:
        limit = max(1, min(int(limit), 1000))
        if not self._path.exists():
            return []
        entries: list[dict] = []
        try:
            for line in self._path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if sender and entry.get("sender", "") != sender:
                    continue
                if group and entry.get("group", "") != group:
                    continue
                if ok is not None and entry.get("ok") != ok:
                    continue
                entries.append(entry)
        except OSError:
            return []
        entries.reverse()
        return entries[:limit]

    def clear(self) -> None:
        try:
            self._path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("审计日志清空失败: %s", exc)

    def stats(self) -> dict:
        entries = self.list_entries(limit=1000)
        ok_count = sum(1 for e in entries if e.get("ok"))
        fail_count = sum(1 for e in entries if not e.get("ok"))
        last_ts = entries[0].get("ts") if entries else None
        return {
            "total": len(entries),
            "ok_count": ok_count,
            "fail_count": fail_count,
            "last_ts": last_ts,
        }
