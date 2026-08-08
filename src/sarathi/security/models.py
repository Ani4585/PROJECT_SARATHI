import contextvars
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Any

class AuthenticationError(Exception):
    """Raised when authentication fails or credentials are invalid."""
    pass

class AuthorizationError(Exception):
    """Raised when an authenticated user lacks required permissions or roles."""
    pass

@dataclass
class UserIdentity:
    user_id: str
    username: str
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_authenticated: bool = True

    def has_role(self, role: str) -> bool:
        return role in self.roles or "admin" in self.roles

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "*:*" in self.permissions or "admin" in self.roles

_SECURITY_CONTEXT: contextvars.ContextVar[Optional[UserIdentity]] = contextvars.ContextVar('security_context', default=None)

class SecurityContext:
    @staticmethod
    def get_current_user() -> Optional[UserIdentity]:
        return _SECURITY_CONTEXT.get()

    @staticmethod
    def set_current_user(user: Optional[UserIdentity]):
        return _SECURITY_CONTEXT.set(user)

    @staticmethod
    def reset(token):
        _SECURITY_CONTEXT.reset(token)
