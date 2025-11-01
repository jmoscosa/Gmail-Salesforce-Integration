from __future__ import annotations
import time, pathlib, requests
from typing import Dict, Optional
from .config import Secrets

class SalesforceAuth:
    """
    Supports:
    - Refresh Token Flow
    """
    def __init__(self, secrets: Secrets, default_expires_in: int = 3600):
        """
        :param secrets: Secrets configuration object.
        :param default_expires_in: Default expiry time (in seconds) for access tokens if not provided by Salesforce (default: 3600).
        """
        s = secrets.get
        self.login_url = s("SF_LOGIN_URL", "https://login.salesforce.com")
        self.instance_url_cfg = s("SF_INSTANCE_URL")
        self.api_version = s("SF_API_VERSION", "v61.0")

        self.client_id = s("SF_CLIENT_ID")
        self.client_secret = s("SF_CLIENT_SECRET")
        self.refresh_token = s("SF_REFRESH_TOKEN")

        self.username = s("SF_USERNAME")
        self.private_key_path = s("SF_PRIVATE_KEY_PATH")
        self.audience = s("SF_AUDIENCE", self.login_url)

        self.default_expires_in = default_expires_in  # Default expiry for access tokens

        if not self.client_id:
            raise ValueError("SF_CLIENT_ID is required for authentication.")
        
        self._access: Optional[Dict[str,str]] = None

    @property
    def access_token(self) -> str:
        self._ensure_token()
        return self._access["access_token"]

    @property
    def instance_url(self) -> str:
        self._ensure_token()
        return self._access["instance_url"]

    @property
    def expires_at(self) -> float:
        self._ensure_token()
        return self._access["expires_at"]

    def _ensure_token(self) -> None:
        if self._access and time.time() < self._access["expires_at"]:
            return  # Token is still valid
        self._refresh()

    def _refresh(self) -> None:
        # Refresh Token flow
        if self.refresh_token and self.client_secret:
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            }
            url = f"{self.login_url}/services/oauth2/token"
            resp = requests.post(url, data=data, timeout=30)

            # Show first 200 chars in case it's HTML or an error wrapper
            preview = resp.text[:200].replace("\n", " ")  

            # Must be JSON and include access_token
            try:
                tok = resp.json()
            except Exception as e:
                raise RuntimeError(f"Token response was not JSON (status {resp.status_code}). Head: {preview}") from e

            if "access_token" not in tok:
                raise RuntimeError(f"Token JSON missing access_token. Keys: {list(tok.keys())}. Full head: {preview}")

            self._access = {
                "access_token": tok["access_token"],
                "instance_url": tok.get("instance_url") or (self.instance_url_cfg or ""),
                "expires_at": time.time() + int(tok.get("expires_in", 3600)) - 30,
            }
            if not self._access["instance_url"]:
                raise RuntimeError(
                    "instance_url missing. Add SF_INSTANCE_URL to secrets or ensure the token response includes it."
                )
            return
    @classmethod
    def get_session(cls, *, secrets_path: str | None = None, profile: str = "dev"):
        """
        Returns a simple authenticated session with a base_url attribute set to the
        Salesforce instance URL and Authorization header preconfigured.
        """
        secrets = Secrets(path=secrets_path, profile=profile)
        auth = cls(secrets=secrets)

        sess = requests.Session()
        sess.headers.update({
            "Authorization": f"Bearer {auth.access_token}",
            "Content-Type": "application/json"
        })
        # Attach base_url so http.sf_request can compose full URLs
        sess.base_url = auth.instance_url  # type: ignore[attr-defined]
        return sess
