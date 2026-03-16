"""
Tenant registry for multi-WABA WhatsApp routing.

Each tenant (company) has its own WhatsApp Business Account (WABA)
with its own phone number, access token, and verify token.

The webhook receives messages from all WABAs at the same URL.
We route to the correct bot handler using the phone_number_id
included in every Meta webhook payload.

Usage (in main.py):
    from .tenants import register_tenant, TenantConfig
    register_tenant(TenantConfig(
        name="Cootradecun",
        phone_number_id=os.getenv("COOTRADECUN_PHONE_NUMBER_ID"),
        access_token=os.getenv("COOTRADECUN_ACCESS_TOKEN"),
        verify_token=os.getenv("COOTRADECUN_VERIFY_TOKEN"),
        handler=handle_cootradecun,
    ))
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Optional


@dataclass
class TenantConfig:
    name: str
    phone_number_id: str
    access_token: str
    verify_token: str
    # Async function(sender_phone, text, message_id, tenant, sender_name) -> None
    handler: Callable[..., Awaitable[None]] = field(default=None, repr=False)


# phone_number_id → TenantConfig
_REGISTRY: dict[str, TenantConfig] = {}


def register_tenant(config: TenantConfig) -> None:
    """Register a tenant. Called once at startup."""
    if not config.phone_number_id:
        import logging
        logging.getLogger(__name__).warning(
            f"⚠️ Tenant '{config.name}' has no phone_number_id — skipping registration."
        )
        return
    _REGISTRY[config.phone_number_id] = config
    import logging
    logging.getLogger(__name__).info(
        f"✅ Tenant registered: {config.name} (phone_id=...{config.phone_number_id[-4:]})"
    )


def get_tenant(phone_number_id: str) -> Optional[TenantConfig]:
    """Look up a tenant by phone_number_id (from Meta webhook payload)."""
    return _REGISTRY.get(phone_number_id)


def get_tenant_by_verify_token(token: str) -> Optional[TenantConfig]:
    """Look up a tenant by verify_token (used during webhook verification GET)."""
    return next((t for t in _REGISTRY.values() if t.verify_token == token), None)


def registered_tenants() -> list[TenantConfig]:
    return list(_REGISTRY.values())
