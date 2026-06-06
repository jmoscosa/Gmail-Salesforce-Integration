# Gmail → Salesforce Integration — Project Context

**Date:** 2026-03-14
**Author:** Jesus Moscosa
**Repo:** `Gmail_Salesfore_Integration` (Python 3.11+, managed with `uv`)
**Package name:** `gmail-salesforce-sync` v0.1.0

---

## What This Project Does

Automatically pulls promotional/marketing emails from Gmail, stages them in a data warehouse (DuckDB or Postgres), and syncs sender data into Salesforce as Contacts (with optional Cases). The goal is to eliminate manual data entry and capture marketing campaign data from companies we've opted into.

**High-level flow:**
```
Gmail API → fetch message metadata → staging DB → Salesforce (Contact + Case)
```

---

## Project Structure

```
src/
├── gmail_sync/          # Gmail extraction layer
│   ├── auth.py          # OAuth2 via token.json / client_secret.json
│   ├── gmail_api.py     # list_messages_ids(), get_metadata_headers()
│   ├── pipeline.py      # fetch_messages() orchestrator
│   └── __main__.py      # CLI: python -m gmail_sync [--promotions-unread|--inbox-unread|...]
│
├── data_warehouse/      # Staging layer
│   ├── backends/
│   │   ├── backend.py          # StagingBackend protocol + StagingBackendConfig dataclass
│   │   ├── duckdb_backend.py   # DuckDBStagingBackend (default: data/staging.duckdb)
│   │   └── postgres_backend.py # PostgresStagingBackend (psycopg2)
│   ├── repos/
│   │   ├── gmail_repo.py       # GmailRepo — DuckDB: raw.raw_gmail_messages
│   │   └── gmail_repo_pg.py    # GmailRepoPg — Postgres: integrations.gmail_messages_raw
│   └── runner.py               # CLI: python -m data_warehouse [--backend duckdb|postgres]
│
├── salesforce_sync/     # Salesforce write layer
│   ├── config.py        # Secrets loader (.secrets/salesforce.json, profile-based)
│   ├── auth.py          # SalesforceAuth — Refresh Token flow, token caching
│   ├── http.py          # sf_request() — authenticated HTTP helper
│   ├── contacts.py      # find_contact_by_email(), create_contact(), contact_exists()
│   ├── cases.py         # create_case(), create_case_for_contact()
│   └── pipeline.py      # auth_check() + CLI: python -m salesforce_sync --auth-check
│
config/
└── settings.yaml        # Default query: "category:promotions is:unread", max_results: 25

.secrets/                # NOT committed
├── client_secret.json   # Google OAuth2 app credentials
├── token.json           # Cached Gmail access/refresh token
└── salesforce.json      # SF credentials by profile (dev/stage/prod)
```

---

## Layer Status

### Layer 1 — Gmail Extraction (`gmail_sync`) ✅ DONE
- OAuth2 auth with token refresh
- Fetches message metadata: `message_id`, `sender`, `subject`, `date_received`, `snippet`
- CLI with preset queries (`--promotions-unread`, `--inbox-unread`, `--inbox-1d`) or custom `--q`
- Default scope: `gmail.readonly`

### Layer 2 — Data Warehouse / Staging (`data_warehouse`) ✅ DONE (dual backend)
- **Backend protocol** (`StagingBackend`): DB-agnostic interface with `execute`, `executemany`, `fetchall`
- **DuckDB backend**: File-based, default path `data/staging.duckdb` (env: `STAGE_DUCKDB_PATH`)
  - Table: `raw.raw_gmail_messages` — uses `INSERT OR REPLACE` (upsert by `message_id`)
- **Postgres backend**: `psycopg2`, default DSN from env vars (`POSTGRES_USER/PASSWORD/HOST/PORT/DB`)
  - Table: `integrations.gmail_messages_raw` — stores metadata as `JSONB payload`, `ON CONFLICT DO NOTHING`
  - Schema: `gmail_message_id (PK), thread_id (NULL), received_at (NULL), payload_json (JSONB), ingested_at`
- **Runner CLI**: `python -m data_warehouse --backend [duckdb|postgres] --q "..." --max 100`
- **TODO in gmail_repo_pg.py**: `thread_id` and `received_at` are always `NULL` — need to be populated from Gmail API

### Layer 3 — Salesforce Sync (`salesforce_sync`) ✅ AUTH + CONTACTS + CASES DONE
- **Auth**: Refresh Token OAuth2 flow, auto-refresh with 30s buffer, profile-based secrets
- **Secrets file**: `.secrets/salesforce.json` → `{ "profiles": { "dev": { "SF_CLIENT_ID": ..., "SF_REFRESH_TOKEN": ..., ... } } }`
- **Required env/secrets keys**: `SF_CLIENT_ID`, `SF_CLIENT_SECRET`, `SF_REFRESH_TOKEN`, `SF_INSTANCE_URL`
- **Contacts**: `find_contact_by_email()`, `create_contact()`, `contact_exists()` (find-or-create)
- **Cases**: `create_case()`, `create_case_for_contact()` (tied to a ContactId)
- **HTTP helper**: `sf_request(method, path, params, json)` — wraps `SalesforceAuth.get_session()`
- **API version**: `v62.0` (in `config.py`)
- **CLI**: `python -m salesforce_sync --auth-check --profile dev`

---

## What Is NOT Done Yet

1. **End-to-end pipeline** — No code connects Layer 2 (staging DB) to Layer 3 (Salesforce). The full flow `staged messages → parse sender email → contact_exists() → create_case()` has not been implemented.
2. **`thread_id` / `received_at`** in `GmailRepoPg` — always stored as `NULL`, needs parsing from Gmail API response.
3. **Preset fetcher functions** in `gmail_sync/pipeline.py` — commented out (`fetch_unread_promotions`, `fetch_inbox_unread`, `fetch_inbox_last_day`).
4. **Sender email parsing** — the `sender` field from Gmail is raw (`"Name <email@domain.com>"`) and needs to be parsed to extract a clean email address before passing to Salesforce.
5. **Scheduling / automation** — no cron, no scheduler, runs are manual via CLI.
6. **Tests** — `pytest` is in dev deps but no test files exist yet.
7. **Error handling / dead-letter queue** for failed SF writes.

---

## Key Design Decisions

- **DuckDB as staging default** — fast, file-based, no server needed for dev; Postgres is the production target.
- **Backend protocol pattern** — `StagingBackend` is a `Protocol` so repos are DB-agnostic; swap backends by passing a different implementation.
- **JSONB payload in Postgres** — raw metadata stored as a blob for flexibility; structured columns (`thread_id`, `received_at`) are reserved but not yet populated.
- **Profile-based SF secrets** — supports `dev`/`stage`/`prod` in a single JSON file.
- **Read-only Gmail scope** — `gmail.readonly` only; no write access to Gmail.

---

## Dependencies

```toml
duckdb>=1.4.4
google-api-python-client>=2.184.0
google-auth>=2.41.1
google-auth-oauthlib>=1.2.2
psycopg2-binary>=2.9.11
requests>=2.32.0
```
Dev: `pytest`, `ruff`, `black`, `isort`

---

## How to Run

```bash
# Activate venv
.venv/Scripts/activate    # Windows

# Fetch Gmail messages (print to stdout)
python -m gmail_sync --promotions-unread --max 10

# Stage to DuckDB (default)
python -m data_warehouse --max 50

# Stage to Postgres
python -m data_warehouse --backend postgres --max 50

# Check Salesforce auth
python -m salesforce_sync --auth-check --profile dev
```

---

## Next Logical Step

Build the **end-to-end pipeline** that:
1. Reads staged messages from `integrations.gmail_messages_raw` (Postgres)
2. Parses the `sender` field to extract a clean email address
3. Calls `contact_exists()` to find or create the Salesforce Contact
4. Calls `create_case_for_contact()` to log the email as a Case in Salesforce
