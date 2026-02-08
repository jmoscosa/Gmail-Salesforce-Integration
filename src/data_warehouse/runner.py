from __future__ import annotations
import argparse
from typing import List, Optional 
from .backends.backend import StagingBackendConfig
from .backends.duckdb_backend import DuckDBStagingBackend, default_duckdb_path
from .repos.gmail_repo import GmailRepo
from gmail_sync.pipeline import fetch_messages

def run_once(*, query: str, label_ids: Optional[List[str]], max_results: int, db_path: str) -> None:
    """
    Run the data warehouse pipeline once to fetch Gmail messages and store them in the staging area.
    """
    # Step 1: Fetch messages from Gmail
    messages = fetch_messages(query=query, label_ids=label_ids, max_results=max_results)
    print(f"Fetched {len(messages)} messages from Gmail.")

    # Step 2: Store messages in the staging area
    backend = DuckDBStagingBackend(StagingBackendConfig(dsn=db_path))
    try:
        repo = GmailRepo(backend=backend)
        inserted_count = repo.upsert_raw_messages(messages)
        print(f"[stage] Inserted {inserted_count} messages into the staging area. To DuckDB at {db_path}")

        # Read back to verify landing 
        staged = repo.read_raw_messages(limit=min(max_results, 50))
        print(f"[verify] Verified staging of {len(staged)} messages.")
    except Exception as e:
        print(f"Error inserting messages: {e}")
        raise
    finally:
        backend.close()

def main() -> None: 
    p = argparse.ArgumentParser(description="Gmail -> DuckDB staging")
    p.add_argument("--q",default="in:inbox newer_than:7d", help="Gmail search query")
    p.add_argument("--labels", nargs="*", default=None, help="Gmail label IDs to filter by")
    p.add_argument("--max", type=int, default=100, help="Max number of messages to fetch")
    p.add_argument("--db", default=default_duckdb_path(), help="Path to DuckDB database file")
    args = p.parse_args()
    run_once(query=args.q, label_ids=args.labels, max_results=args.max, db_path=args.db)

if __name__ == "__main__":    main()