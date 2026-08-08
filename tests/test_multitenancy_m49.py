import asyncio
import pytest
from sarathi.multitenancy import (
    TenantIdentity,
    TenantContext,
    TenantContextError,
    TenantResolver,
    require_tenant,
)

def test_tenant_resolver_header_and_host():
    headers = {"X-Tenant-ID": "tenant_999"}
    assert TenantResolver.resolve_from_header(headers) == "tenant_999"

    host = "corp.sarathi.io"
    assert TenantResolver.resolve_from_host(host) == "corp"

def test_require_tenant_decorator_sync():
    tenant = TenantIdentity(tenant_id="t100", tenant_name="Acme Inc")
    token = TenantContext.set_current_tenant(tenant)

    try:
        @require_tenant
        def get_tenant_data():
            curr = TenantContext.get_current_tenant()
            return f"data_{curr.tenant_id}"

        assert get_tenant_data() == "data_t100"
    finally:
        TenantContext.reset(token)

    @require_tenant
    def unauthenticated_fn():
        return "ok"

    with pytest.raises(TenantContextError):
        unauthenticated_fn()

def test_require_tenant_decorator_async():
    async def _test():
        tenant = TenantIdentity(tenant_id="t200", tenant_name="Beta Corp")
        token = TenantContext.set_current_tenant(tenant)

        try:
            @require_tenant
            async def fetch_tenant_async():
                curr = TenantContext.get_current_tenant()
                return f"async_{curr.tenant_id}"

            assert await fetch_tenant_async() == "async_t200"
        finally:
            TenantContext.reset(token)

    asyncio.run(_test())
