from __future__ import annotations
import json, os, pathlib
from typing import Optional, Any, Dict

# Path to the default Salesforce configuration file in the user's home directory
DEFAULT_CONFIG_PATH = ".secrets/salesforce.json"
# Default Salesforce API version
API_VERSION = "v61.0"

class Secrets:
    """
    Loads Salesforce configuration from a JSON file.
    Precedence:
    1) CLI provided path (passed as kwargs to get_dict)
    2) Environment variable 'SALESFORCE_CONFIG_PATH'
    3) Default path in user's home directory. Ex: ~/.secrets/salesforce.json
    """

    def __init__(self, path: Optional[str] = None, profile: str = "dev"):
        self.path = pathlib.Path(path or os.getenv("SALESFORCE_CONFIG_PATH") or DEFAULT_CONFIG_PATH)
        self.profile = profile
        if not self.path.exists():
            raise FileNotFoundError(
                f"Salesforce config file not found at {self.path}. Create it from {DEFAULT_CONFIG_PATH}.example"
            )
        with self.path.open("r", encoding = "utf-8") as f:
            raw = json.load(f)

        self._profiles = raw.get("profiles", {})
        if self.profile not in self._profiles:
            raise ValueError(f"Profile '{self.profile}' not found in Salesforce config file.")  
        self._active = self._profiles[profile] or {}

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
            return self._active.get(key, default)

    def get_dict(self, **overrides: Any) -> Dict[str, Any]:
            data = dict(self._active)
            data.update({k: v for k, v in overrides.items() if v is not None})
            return data