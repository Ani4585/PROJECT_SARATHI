import contextvars
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

class TenantContextError(Exception):
    """Raised when an operation requires an active tenant context."""
    pass

@dataclass
class TenantIdentity:
    tenant_id: str
    tenant_name: str
    isolation_level: str = "SHARED_SCHEMA"  # "SHARED_SCHEMA", "SEPARATE_SCHEMA", "DATABASE_PER_TENANT"
    config: Dict[str, Any] = field(default_factory=dict)

_TENANT_CONTEXT: contextvars.ContextVar[Optional[TenantIdentity]] = contextvars.ContextVar('tenant_context', default=None)

class TenantContext:
    @staticmethod
    def get_current_tenant() -> Optional[TenantIdentity]:
        return _TENANT_CONTEXT.get()

    @staticmethod
    def set_current_tenant(tenant: Optional[TenantIdentity]):
        return _TENANT_CONTEXT.set(tenant)

    @staticmethod
    def reset(token):
        _TENANT_CONTEXT.reset(token)
