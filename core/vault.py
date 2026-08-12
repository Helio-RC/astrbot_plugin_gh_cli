"""Fernet-encrypted credential vault.

Secrets are stored as a single Fernet token in secrets.json (0600). The
master key comes from the ASTRBOT_GH_MASTER_KEY env var, or is generated
randomly and persisted to master.key (0600) with a warning.
"""

import json
import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

MASTER_KEY_ENV = "ASTRBOT_GH_MASTER_KEY"
SECRETS_FILE = "secrets.json"
KEY_FILE = "master.key"


class Vault:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.fernet = Fernet(self._load_or_create_master_key())
        self._secrets_path = self.data_dir / SECRETS_FILE
        self._decrypt_failed = False
        self._data = self._load()

    def _load_or_create_master_key(self) -> bytes:
        env_key = os.environ.get(MASTER_KEY_ENV)
        if env_key:
            return env_key.encode()
        key_file = self.data_dir / KEY_FILE
        if key_file.exists():
            return key_file.read_bytes()
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        key_file.chmod(0o600)
        logger.warning(
            f"未检测到环境变量 {MASTER_KEY_ENV}，已自动生成随机主密钥: {key_file}。"
            "重启后如需解密已有数据请保留该文件。"
        )
        return key

    def _load(self) -> dict:
        if not self._secrets_path.exists():
            return {}
        try:
            token = self._secrets_path.read_text().strip()
            if not token:
                return {}
            return json.loads(self.fernet.decrypt(token.encode()).decode())
        except (InvalidToken, ValueError):
            self._decrypt_failed = True
            logger.error("secrets.json 解密失败，请检查主密钥是否正确。")
            return {}

    def _save(self) -> None:
        if self._decrypt_failed:
            raise RuntimeError(
                "secrets.json 解密失败，拒绝覆盖已有凭据。请检查主密钥。"
            )
        payload = json.dumps(self._data, ensure_ascii=False)
        token = self.fernet.encrypt(payload.encode()).decode()
        self._secrets_path.write_text(token)
        self._secrets_path.chmod(0o600)

    def set_shared_token(self, token: str) -> None:
        self._data["shared_token"] = token
        self._save()

    def get_shared_token(self) -> str | None:
        return self._data.get("shared_token")

    def set_personal_token(self, name: str, token: str) -> None:
        self._data.setdefault("personal_tokens", {})[name] = token
        self._save()

    def get_personal_token(self, name: str) -> str | None:
        return self._data.get("personal_tokens", {}).get(name)

    def list_personal_token_names(self) -> list[str]:
        return sorted(self._data.get("personal_tokens", {}).keys())

    def remove_personal_token(self, name: str) -> None:
        self._data.get("personal_tokens", {}).pop(name, None)
        self._save()

    def set_binding(self, user_key: str, name: str) -> None:
        self._data.setdefault("bindings", {})[user_key] = name
        self._save()

    def get_binding(self, user_key: str) -> str | None:
        return self._data.get("bindings", {}).get(user_key)

    def remove_binding(self, user_key: str) -> None:
        self._data.get("bindings", {}).pop(user_key, None)
        self._save()
