from __future__ import annotations
from typing import Dict, List, Optional
from googleapiclient.errors import HttpError 

def list_messages_ids(service, *, q: str ="", label_ids: Optional[List[str]] = None, max_results: int = 50) -> List[str]:
    """List message IDs."""
    try:
        label_ids = label_ids or []
        ids: List[str] = []
        req = service.users().messages().list(
            userId="me", q=q, labelIds=label_ids, maxResults=min(max_results,500)
            )
        while req and len(ids) < max_results:
            res = req.execute()
            ids.extend(m["id"] for m in res.get("messages", []))
            if len(ids) >= max_results:
                break
            req = service.users().messages().list_next(req, res)
        return ids[:max_results]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    
def get_metadata_headers(service, message_id: str) -> Dict[str, str]:
    """Get metadata headers (From, Subject, Date) for a given message ID."""
    try:
        msg = service.users().messages().get(
            userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject", "Date"]
            ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", []) if h["name"] in {"From", "Subject", "Date"}}
        return {"Id": msg.get("id", ""),
                "From": headers.get("From", ""),
                "Subject": headers.get("Subject", ""),
                "Date": headers.get("Date", ""),
                "Snippet": msg.get("snippet", "")}
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {}

def get_headers_for_ids(service, ids: List[str]) -> List[Dict[str, str]]:
    """Get metadata headers for a list of message IDs."""
    out: List[Dict[str, str]] = []
    for mid in ids:
        try:
            out.append(get_metadata_headers(service, mid))
        except HttpError as error:
            print(f"An error occurred: {error}")
    return out  