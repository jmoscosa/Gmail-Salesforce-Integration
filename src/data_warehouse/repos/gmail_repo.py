from __future__ import annotations 
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List 
from ..backends.backend import StagingBackend 

@dataclass 
class GmailRepo:
    """
    Repository for Gmail data. 
    Responsible for storing and retrieving Gmail data from the staging area. 
    """
    backend: StagingBackend 
    schema: str = "raw"
    table: str = "raw_gmail_messages"

    def _qual(self) -> str:
        """
        Return the qualified table name for the Gmail data.
        """
        return f"{self.schema}.{self.table}"
    
    def ensure_schema(self) -> None:
        """
        Ensure the schema exists in the staging area.
        """
        sql = f"CREATE SCHEMA IF NOT EXISTS {self.schema}"
        self.backend.execute(sql)

        gmail_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._qual()} (
            message_id VARCHAR PRIMARY KEY,
            sender VARCHAR,
            subject VARCHAR,
            date_received VARCHAR,
            snippet VARCHAR,
            ingested_at TIMESTAMP
        )"""
        self.backend.execute(gmail_table_sql)

    def upsert_raw_messages(self, messages: Iterable[Dict[str,str]]) -> int:
        """
        Upsert raw Gmail messages into the staging area.
        """
        self.ensure_schema()
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
        rows: list[tuple] = []
        for msg in messages:
            mid = msg.get("message_id", "").strip() 
            if not mid:
                continue  # Skip messages without a valid message_id
            
            rows.append((
                mid,
                msg.get("sender", "").strip(),
                msg.get("subject", "").strip(),
                msg.get("date_received", "").strip(),
                msg.get("snippet", "").strip(),
                now
            ))
        if not rows:
            return 0  # No valid messages to upsert
        
        self.backend.executemany(
            f"""
            INSERT OR REPLACE INTO {self._qual()} 
            (message_id, sender, subject, date_received, snippet, ingested_at)
            VALUES (?,?,?,?,?,?)
            """,
            rows
        )
        return len(rows)
    
    def read_raw_messages(self,*,limit: int =100) -> List[Dict[str, str]]:
        """
        Read raw Gmail messages from the staging area.
        """
        self.ensure_schema()

        sql = f"SELECT message_id, sender, subject, date_received, snippet FROM {self._qual()} LIMIT ?"
        results = self.backend.fetchall(sql, [limit])
        out: List[Dict[str, str]] = []
        for (mid, sender, subject, date_received, snippet) in results:
            out.append({
                "message_id": mid,
                "sender": sender,
                "subject": subject,
                "date_received": date_received,
                "snippet": snippet
            }
        )
        return out