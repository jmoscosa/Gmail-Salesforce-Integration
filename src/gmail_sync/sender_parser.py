from __future__ import annotations
from email.utils import parseaddr
from typing import Optional


def parse_sender(raw_sender: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse a raw Gmail "From" header into (display_name, email_address).

    Uses Python's stdlib email.utils.parseaddr, which is purpose-built for
    RFC-compliant email "From" headers. Handles edge cases like quoted display
    names, missing brackets, and addresses without a display name.

    Examples:
        "Lev from ReciPal <lev@recipal.com>"      -> ("Lev from ReciPal", "lev@recipal.com")
        "Marriott Bonvoy <mb@email-marriott.com>" -> ("Marriott Bonvoy", "mb@email-marriott.com")
        "just-email@domain.com"                   -> (None, "just-email@domain.com")
        ""                                         -> (None, None)

    Returns:
        Tuple of (display_name, email_address). Either can be None if parsing
        fails or the input is malformed.
    """
    if not raw_sender or not raw_sender.strip():
        return (None, None)

    name, email = parseaddr(raw_sender)
    # parseaddr returns empty strings on failure — normalize to None for consistency
    return (name or None, email or None)