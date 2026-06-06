from __future__ import annotations
import json, os, pathlib
from typing import Optional, Any, Dict

DEFAULT_CONFIG_PATH = ".secrets/postgres.json"

class PostgresSecrets:
    """
    Loads Postgres configuration from a JSON file.
    Precedence:
    1) CLI provided path (passed to constructor)
    2) Environment variable 'POSTGRES_CONFIG_PATH'
    3) Default path: .secrets/postgres.json
    """

    def __init__(self, path: Optional[str] = None, profile: str = "local"):
        self.path = pathlib.Path(path or os.getenv("POSTGRES_CONFIG_PATH") or DEFAULT_CONFIG_PATH)
        self.profile = profile
        if not self.path.exists():
            raise FileNotFoundError(
                f"Postgres config file not found at {self.path}. Create it from {DEFAULT_CONFIG_PATH}.example"
            )
        with self.path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        self._profiles = raw.get("profiles", {})
        if self.profile not in self._profiles:
            raise ValueError(f"Profile '{self.profile}' not found in Postgres config file.")
        self._active = self._profiles[profile] or {}

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._active.get(key, default)

    def get_dict(self, **overrides: Any) -> Dict[str, Any]:
        data = dict(self._active)
        data.update({k: v for k, v in overrides.items() if v is not None})
        return data

    def build_dsn(self) -> str:
        user     = self.get("POSTGRES_USER",     "postgres")
        password = self.get("POSTGRES_PASSWORD", "postgres")
        host     = self.get("POSTGRES_HOST",     "localhost")
        port     = self.get("POSTGRES_PORT",     "5432")
        database = self.get("POSTGRES_DB",       "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"