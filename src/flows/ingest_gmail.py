"""
Prefect flow: ingest Gmail messages into Postgres staging table.

This flow wraps the existing extraction + load logic (no new business logic
introduced). It exists to add orchestration features: scheduling, retries,
observability via the Prefect UI, and run history.

Run manually:
    python -m flows.ingest_gmail
"""
from __future__ import annotations

from prefect import flow, task
from prefect.logging import get_run_logger

from data_warehouse.backends.backend import StagingBackendConfig
from data_warehouse.backends.postgres_backend import (
    PostgresStagingbackend,
    default_postgres_dsn,
)
from data_warehouse.repos.gmail_repo_pg import GmailRepoPg
from gmail_sync.pipeline import fetch_messages


# ─── Configuration (hardcoded for now, will become flow params later) ──────────
QUERY = "in:inbox newer_than:7d"
MAX_RESULTS = 25
POSTGRES_PROFILE = "local"   # switch to "vps" later


# ─── Tasks ─────────────────────────────────────────────────────────────────────
@task(name="fetch-gmail-messages", retries=2, retry_delay_seconds=10)
def fetch_gmail_messages_task(query: str, max_results: int) -> list[dict]:
    """Pull messages from Gmail API. Retries twice on transient failures."""
    logger = get_run_logger()
    logger.info(f"Fetching up to {max_results} messages with query: {query!r}")
    messages = fetch_messages(query=query, label_ids=None, max_results=max_results)
    logger.info(f"Fetched {len(messages)} messages from Gmail.")
    return messages


@task(name="upsert-to-postgres")
def upsert_to_postgres_task(messages: list[dict], profile: str) -> int:
    """Idempotently upsert messages into integrations.gmail_messages_raw."""
    logger = get_run_logger()
    dsn = default_postgres_dsn(profile=profile)
    logger.info(f"Connecting to Postgres via profile '{profile}'")

    backend = PostgresStagingbackend(StagingBackendConfig(dsn=dsn))
    try:
        repo = GmailRepoPg(backend=backend)
        inserted = repo.upsert_messages(messages)
        logger.info(f"Upserted {inserted} messages into staging.")
        return inserted
    finally:
        backend.close()


# ─── Flow ──────────────────────────────────────────────────────────────────────
@flow(name="ingest-gmail")
def ingest_gmail_flow() -> dict:
    """End-to-end Gmail → Postgres ingestion."""
    logger = get_run_logger()
    logger.info("Starting Gmail ingestion flow")

    messages = fetch_gmail_messages_task(QUERY, MAX_RESULTS)
    inserted = upsert_to_postgres_task(messages, POSTGRES_PROFILE)

    summary = {"fetched": len(messages), "inserted": inserted}
    logger.info(f"Flow complete: {summary}")
    return summary


if __name__ == "__main__":
    ingest_gmail_flow.serve(
        name="ingest-gmail-local",
        cron="0 * * * *",
        tags=["gmail", "ingestion","local"],
        description="Ingest Gmail messages into Postgres staging table (local version).",
    )