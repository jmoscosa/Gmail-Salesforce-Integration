from typing import Optional, Dict, Any
from .http import sf_request
from .config import API_VERSION

def _soql(query: str) -> Dict[str, Any]:
    """
    Executes a SOQL query against the Salesforce API.

    Args:
        query (str): The SOQL query string.
        Ex. "SELECT Id, Email FROM Contact WHERE Email = "
    Returns:
        Dict[str, Any]: The JSON response from the Salesforce API.
    """
    return sf_request("GET", f"/services/data/{API_VERSION}/query", params={"q": query})

def find_contact_by_email(email: str, account_id: Optional[str] = None) -> Optional[str]:
    """
    Finds a Salesforce Contact by email address, optionally within a specific Account.
    """
    safe_email = email.replace("'", "\\'")
    where = f"Email = '{safe_email}'"
    if account_id:
        where += f" AND AccountId = '{account_id}'"
    q = f"SELECT Id FROM Contact WHERE {where} LIMIT 1"
    result = _soql(q)
    records = result.get("records", [])
    return records[0]["Id"] if records else None

def create_contact(payload: Dict[str, Any]) -> str:
    """
    Creates a new Salesforce Contact with the given payload.

    Args:
        payload (Dict[str, Any]): The data for the new Contact.

    Returns:
        str: The ID of the newly created Contact.
    """
    res = sf_request("POST", f"/services/data/{API_VERSION}/sobjects/Contact", json=payload)
    if not res.get("success"):
        raise Exception(f"Failed to create Contact: {res}")
    return res["id"]

def contact_exists(email: str, defaults: Optional[Dict[str, Any]] = None, account_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks if a Salesforce Contact exists by email. If not, creates one with the provided defaults.

    Returns:
        Dict: A dictionary with 'found' (bool) indicating if the contact was found and 'contact_id' (str) for the Contact's ID.
    """
    cid = find_contact_by_email(email,account_id)
    if cid:
        return {"found": True, "contact_id": cid}

    data = dict(defaults or {})                                 
    data.setdefault("Email", email)
    data.setdefault("LastName", email.split("@")[0] or "NoLastName")
    if account_id and "AccountId" not in data:
        data["AccountId"] = account_id

    cid = create_contact(data)
    return {"found": False, "contact_id": cid}
