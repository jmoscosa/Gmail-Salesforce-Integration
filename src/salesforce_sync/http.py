from typing import Dict, Any, Optional
from .auth import SalesforceAuth


def sf_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Makes an authenticated HTTP request to the Salesforce API.

    Args:
        method: HTTP method (e.g., 'GET', 'POST').
        path: Path relative to the Salesforce instance URL (e.g., '/services/data/v62.0/query').
        params: Query parameters.
        json: JSON body.

    Returns:
        The parsed JSON response (or empty dict if no content).
    """
    # Acquire an authenticated session bound to the Salesforce instance URL
    sess = SalesforceAuth.get_session()
    url = f"{sess.base_url}/{path.lstrip('/')}"
    response = sess.request(method=method, url=url, params=params, json=json)
    response.raise_for_status()
    return response.json() if response.content else {}
