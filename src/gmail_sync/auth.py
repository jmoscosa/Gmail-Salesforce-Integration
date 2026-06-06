from __future__ import annotations
from pathlib import Path
from typing import Final
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Paths
ROOT: Final[Path] = Path(__file__).parents[2]
SECRETS_DIR: Final[Path] = ROOT / ".secrets"
CLIENT_SECRET: Final[Path] = SECRETS_DIR / "client_secret.json"
TOKEN_FILE: Final[Path] = SECRETS_DIR / "token.json"

# Scope * If switching scopes, delete the token.json file and re-authenticate.
SCOPES: Final[list[str]] = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    service = build("gmail", "v1", credentials=creds)
    return service