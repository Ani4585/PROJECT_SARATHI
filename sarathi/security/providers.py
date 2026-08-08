import base64
from typing import Dict, Optional
from .models import UserIdentity, AuthenticationError
from .jwt import JWTManager
from .hashing import PasswordHasher

class ApiKeyAuthenticationProvider:
    def __init__(self, api_keys: Dict[str, UserIdentity]):
        self.api_keys = api_keys

    def authenticate(self, api_key: str) -> UserIdentity:
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        raise AuthenticationError("Invalid API Key")

class JWTAuthenticationProvider:
    def __init__(self, jwt_manager: JWTManager):
        self.jwt_manager = jwt_manager

    def authenticate(self, token: str) -> UserIdentity:
        try:
            payload = self.jwt_manager.decode(token)
            user_id = payload.get("sub", "unknown")
            username = payload.get("username", user_id)
            roles = set(payload.get("roles", []))
            permissions = set(payload.get("permissions", []))
            return UserIdentity(user_id=user_id, username=username, roles=roles, permissions=permissions)
        except Exception as e:
            raise AuthenticationError(f"JWT Authentication failed: {str(e)}")

class BasicAuthenticationProvider:
    def __init__(self, user_store: Dict[str, str], user_identities: Dict[str, UserIdentity], hasher: Optional[PasswordHasher] = None):
        self.user_store = user_store # username -> hashed_pass
        self.user_identities = user_identities
        self.hasher = hasher or PasswordHasher()

    def authenticate(self, basic_header: str) -> UserIdentity:
        try:
            if not basic_header.startswith("Basic "):
                raise AuthenticationError("Invalid basic auth header")
            encoded = basic_header[6:].strip()
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
        except Exception:
            raise AuthenticationError("Malformed Basic credentials")

        if username in self.user_store and self.hasher.verify_password(password, self.user_store[username]):
            return self.user_identities.get(username, UserIdentity(user_id=username, username=username))
        raise AuthenticationError("Invalid username or password")
