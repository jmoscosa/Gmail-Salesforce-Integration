from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone 
from typing import List, Dict, Iterable 
from ..backends.backend import StagingBackend
import json 

@dataclass 
class GmailRepoPg:
    """
    Postgres repository for Gmail data.
    Writes to the integrations.gmail_messages_raw table in a Postgres database.
    """
    backend: StagingBackend 
    schema: str = "integrations"
    table: str = "gmail_messages_raw" 

    def _qual(self) -> str:
        """Return the fully qualified table name."""
        return f"{self.schema}.{self.table}" 
    
    def upsert_messages(self, messages: Iterable[Dict[str, str]]) -> int:
        """
        Insert Gmail messages into Postgres.
        - Guardrails for re-running pipelines.
        - Pack flat files (sender, subject, etc.) into a JSON blob.
        """
        now = datetime.now(timezone.utc)
        rows: list[tuple] = []

        for msg in messages: 
            mid = msg.get("message_id", "").strip()
            if not mid:
                continue # Skip messages without a valid message_id 
            #TODO - add thread_id and recevied_at as separate columns for better querying and indexing.
            payload = {
                "sender": msg.get("sender", ""),
                "subject": msg.get("subject", ""),
                "date_received": msg.get("date_received", ""),
                "snippet": msg.get("snippet", "")
            }

            rows.append((
                mid,   #gmail_message_id (primary key)
                None,  #thread_id (optional, for future use)
                None,  # received_at (optional, for future use)
                json.dumps(payload), #payload (JSON blob of the message metadata)
                now,   # ingested_at (timestamp of when the message was ingested into Postgres)
            ))

        if not rows:
            return 0
        
        sql = f"""
            INSERT INTO 
                {self._qual()}
                (gmail_message_id, thread_id, received_at, payload_json, ingested_at)
            VALUES
                (%s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (gmail_message_id) DO NOTHING
        """
        self.backend.executemany(sql, rows)
        return len(rows)    
    
    def read_messages(self, *, limit: int = 100) -> List[Dict]:
        """Read messages from Postgres for testing and validation."""
        sql = f"""
            SELECT gmail_message_id, thread_id, received_at, ingested_at 
            FROM {self._qual()}
            ORDER BY ingested_at DESC
            LIMIT %s
        """
        results = self.backend.fetchall(sql, [limit])
        return[
            {
                "message_id": r[0],
                "thread_id": r[1],
                "received_at": r[2],
                "ingested_at": r[3]
            }
            for r in results
        ]
    
    def fetch_unsynced(self, *, limit: int = 100) -> List[Dict]:
        """
        Fetch messages that have not yet been synced to Salesforce.
        Returns rows where synced_at IS NULL — meaning they are waiting to be processed.
        """
        sql = f"""
            SELECT gmail_message_id, payload_json, ingested_at
            FROM {self._qual()}
            WHERE synced_at IS NULL
            ORDER BY ingested_at ASC
            LIMIT %s
        """
        results = self.backend.fetchall(sql, [limit])
        return [
            {
                "message_id": r[0],
                "payload": r[1],       # JSONB returns as Python dict automatically
                "ingested_at": r[2],
            }
            for r in results
        ]

    def mark_synced(self, message_id: str) -> None:
        """
        Mark a single message as successfully synced to Salesforce by stamping
        synced_at with the current UTC timestamp. Call this AFTER the Salesforce
        write succeeds, not before.
        """
        sql = f"""
            UPDATE {self._qual()}
            SET synced_at = NOW()
            WHERE gmail_message_id = %s
        """
        self.backend.execute(sql, [message_id])