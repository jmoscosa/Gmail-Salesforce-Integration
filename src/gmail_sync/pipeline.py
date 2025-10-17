from __future__ import annotations
from typing import List, Dict, Optional
from .auth import get_gmail_service
from .gmail_api import list_messages_ids, get_headers_for_ids 

def fetch_messages(*, query: str ="", label_ids: Optional[List[str]] = None, max_results: int = 50) -> List[Dict[str, str]]:
    """
    Orchestrate fetching message metadata from Gmail.
    """
    service = get_gmail_service()
    ids = list_messages_ids(service, q=query, label_ids=label_ids, max_results=max_results)
    if not ids:
        return []
    headers = get_headers_for_ids(service, ids)
    return headers

# TODO : Add preset fetcher functions
# def fetch_unread_promotions(max_results: int = 25) -> List[Dict[str, str]]:
#     return fetch_messages(query="category:promotions is:unread", max_results=max_results)


# def fetch_inbox_unread(max_results: int = 25) -> List[Dict[str, str]]:
#     return fetch_messages(query="in:inbox is:unread", max_results=max_results)


# def fetch_inbox_last_day(max_results: int = 25) -> List[Dict[str, str]]:
#     return fetch_messages(query="in:inbox newer_than:1d", max_results=max_results)