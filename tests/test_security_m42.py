import asyncio
import pytest
from sarathi.security import (
    UserIdentity,
    SecurityContext,
    AuthenticationError,
    AuthorizationError,
    JWTManager,
    PasswordHasher,
    constant_time_compare,
    ApiKeyAuthenticationProvider,
    JWTAuthenticationProvider,
    require_auth,
    require_role,
    require_permission,
)

def test_user_identity_permissions():
    user = UserIdentity(user_id="u1", username="alice", roles={"editor"}, permissions={"docs:read", "docs:write"})
    assert user.has_role("editor") is True
    assert user.has_role("admin") is False
    assert user.has_permission("docs:write") is True
    assert user.has_permission("docs:delete") is False

def test_admin_inherits_all_roles_and_permissions():
    admin = UserIdentity(user_id="admin_1", username="root", roles={"admin"})
    assert admin.has_role("any_role") is True
    assert admin.has_permission("any_permission") is True

def test_jwt_manager_encode_decode_flow():
    jwt_mgr = JWTManager(secret_key="my_secret_key", default_ttl=3600)
    token = jwt_mgr.encode({"sub": "user_100", "username": "bob", "roles": ["developer"]})
    
    decoded = jwt_mgr.decode(token)
    assert decoded["sub"] == "user_100"
    assert decoded["username"] == "bob"
    assert "developer" in decoded["roles"]

def test_jwt_manager_expired_token():
    jwt_mgr = JWTManager(secret_key="my_secret_key", default_ttl=-10)
    token = jwt_mgr.encode({"sub": "user_100"})
    
    with pytest.raises(ValueError) as exc_info:
        jwt_mgr.decode(token)
    assert "expired" in str(exc_info.value)

def test_password_hasher_and_constant_time_compare():
    hasher = PasswordHasher()
    hashed = hasher.hash_password("MySecurePassword123!")
    
    assert hasher.verify_password("MySecurePassword123!", hashed) is True
    assert hasher.verify_password("WrongPassword!", hashed) is False
    assert constant_time_compare("secret_token", "secret_token") is True
    assert constant_time_compare("secret_token", "wrong_token") is False

def test_api_key_authentication_provider():
    identity = UserIdentity(user_id="u10", username="service_acct", roles={"service"})
    provider = ApiKeyAuthenticationProvider(api_keys={"secret_api_key_123": identity})

    authenticated_user = provider.authenticate("secret_api_key_123")
    assert authenticated_user.user_id == "u10"

    with pytest.raises(AuthenticationError):
        provider.authenticate("invalid_key")

def test_rbac_decorators():
    user = UserIdentity(user_id="u1", username="editor_user", roles={"editor"}, permissions={"article:edit"})
    token = SecurityContext.set_current_user(user)

    try:
        @require_auth
        def protected_fn():
            return "auth_ok"

        @require_role("editor")
        def edit_fn():
            return "role_ok"

        @require_role("admin")
        def admin_fn():
            return "admin_ok"

        @require_permission("article:edit")
        def perm_fn():
            return "perm_ok"

        assert protected_fn() == "auth_ok"
        assert edit_fn() == "role_ok"
        assert perm_fn() == "perm_ok"

        with pytest.raises(AuthorizationError):
            admin_fn()
    finally:
        SecurityContext.reset(token)

def test_rbac_decorators_async():
    async def _test():
        user = UserIdentity(user_id="u2", username="async_user", roles={"editor"})
        token = SecurityContext.set_current_user(user)

        try:
            @require_role("editor")
            async def async_edit():
                return "async_role_ok"

            assert await async_edit() == "async_role_ok"
        finally:
            SecurityContext.reset(token)

    asyncio.run(_test())
