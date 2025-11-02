from __future__ import annotations
from typing import Optional, Dict, Any
from .http import sf_request
from .config import API_VERSION

def create_case(payload: Dict[str, Any]) -> Optional[str]:
    """
    Create a Salesforce Case with the given payload.

    Required in payload:
        - 'Subject'
        - 'ContactId'

    Common/Recommended fields:
      - 'AccountId' (str)        -> link to the Account (optional)
      - 'Description' (str)      -> body/details
      - 'Origin' (str)           -> e.g., 'Email'
      - 'Status' (str)           -> e.g., 'New'
      - 'Priority' (str)         -> e.g., 'Medium'
    Args:
        payload: A dictionary containing the Case fields and values.

    Returns:
        The ID of the created Case if successful, else None.
    """
    if not payload.get("Subject"):
        raise ValueError("Payload must include 'Subject' field.")
    
    res = sf_request(
        "POST",
        f"/services/data/{API_VERSION}/sobjects/Case/",
        json=payload,
    )
    if not res.get("success"):
        raise RuntimeError(f"Failed to create Case: {res}")
    return res["id"]



def create_case_for_contact(
        *,
        contact_id: str,
        subject: str,
        description: Optional[str] = None,
        account_id: Optional[str] = None,
        origin: str = "Email",
        status: str = "New",
        priority: str = "Medium",
        extra_fields: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Convenience wrapper to create a Case tied to a specific Contact.

    Args:
        contact_id: Salesforce Contact Id the Case should be linked to.
        subject: Case Subject (Email subject here).
        description: Optional Case Description (Email body).
        account_id: Optional Account Id.
        origin: Defaults to 'Email'.
        status: Defaults to 'New'.
        priority: Defaults to 'Medium'.
        extra_fields: Any additional Case fields to set (e.g., RecordTypeId, custom fields).

    Returns:
        The newly created Case Id.
    """
    if not contact_id:
        raise ValueError("contact_id is required to create a Case.")
    if not subject:
        raise ValueError("subject is required to create a Case.")
    
    payload: Dict[str, Any] = {
        "ContactId": contact_id,
        "Subject": subject,
        "Origin": origin,
        "Status": status,
        "Priority": priority,
    }
    if account_id:
        payload["AccountId"] = account_id
    if description:
        payload["Description"] = description    
    if extra_fields:
        payload.update(extra_fields)

    return create_case(payload)