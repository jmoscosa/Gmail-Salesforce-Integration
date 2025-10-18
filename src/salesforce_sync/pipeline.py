from __future__ import annotations
import argparse, requests
from .config import Secrets 
from .auth import SalesforceAuth

def auth_check(profile: str, secrets_file: str | None) -> dict:
    secrets = Secrets(path=secrets_file, profile=profile)
    auth = SalesforceAuth(secrets=secrets)
    token = auth.access_token

    # Identity endpoint on login domain
    r = requests.get(
        f"{secrets.get('SF_LOGIN_URL') or 'https://login.salesforce.com'}/services/oauth2/userinfo",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    r.raise_for_status()
    me = r.json()

    return {
        "instance_url": auth.instance_url,
        "username": me.get("preferred_username") or me.get("email"),
        "user_id": me.get("user_id"),
        "organization_id": me.get("organization_id"),
        "expires_at": auth.expires_at,
        "api_version": secrets.get("SF_API_VERSION") or "v61.0",
        "profile": profile
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--auth-check", action="store_true", help="Fetch a token and print identity + instance_url.")
    p.add_argument("--profile", default="dev", help="Profile name in secrets file (e.g. dev, stage, prod).")
    p.add_argument("--secrets", default=None, help="Path to secrets JSON. Defaults to .secrets/salesforce.json")
    args = p.parse_args()

    if args.auth_check:
        info = auth_check(args.profile, args.secrets)
        print(info)

if __name__ == "__main__":
    main()