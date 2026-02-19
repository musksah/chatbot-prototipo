"""
API dependencies.

Simplified auth dependency for the chatbot prototype.
In production, replace with JWT-based authentication.
"""

from typing import Optional


class CurrentUser:
    """Minimal user representation for the prototype."""
    def __init__(self, username: str = "admin"):
        self.username = username


async def require_any_role() -> CurrentUser:
    """
    Simplified auth dependency — allows all requests.

    TODO: Replace with JWT-based authentication when moving to production.
    Example implementation:
        - Validate Bearer token from Authorization header
        - Decode JWT and extract user/role
        - Raise 401 if invalid
    """
    return CurrentUser(username="admin")
