from typing import List, Optional
from .models import GatewayContext

class GatewayInterceptor:
    async def pre_handle(self, ctx: GatewayContext) -> bool:
        """Returns True to continue pipeline, False to short-circuit."""
        return True

    async def post_handle(self, ctx: GatewayContext):
        pass

class CORSInterceptor(GatewayInterceptor):
    def __init__(self, allow_origins: Optional[List[str]] = None, allow_methods: Optional[List[str]] = None, allow_headers: Optional[List[str]] = None):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]

    async def pre_handle(self, ctx: GatewayContext) -> bool:
        origin = ctx.request.headers.get("origin", "*")
        if ctx.request.method.upper() == "OPTIONS":
            ctx.response.status_code = 204
            ctx.response.headers["Access-Control-Allow-Origin"] = origin if "*" in self.allow_origins else (origin if origin in self.allow_origins else "")
            ctx.response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            ctx.response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            return False
        return True

    async def post_handle(self, ctx: GatewayContext):
        origin = ctx.request.headers.get("origin", "*")
        ctx.response.headers["Access-Control-Allow-Origin"] = origin if "*" in self.allow_origins else (origin if origin in self.allow_origins else "")

class LoggingInterceptor(GatewayInterceptor):
    def __init__(self):
        self.logs = []

    async def pre_handle(self, ctx: GatewayContext) -> bool:
        self.logs.append(f"INBOUND {ctx.request.method} {ctx.request.path}")
        return True

    async def post_handle(self, ctx: GatewayContext):
        self.logs.append(f"OUTBOUND {ctx.response.status_code}")

class AuthInterceptor(GatewayInterceptor):
    def __init__(self, token_verifier: Optional[Any] = None):
        self.token_verifier = token_verifier

    async def pre_handle(self, ctx: GatewayContext) -> bool:
        auth_header = ctx.request.headers.get("authorization", "")
        if self.token_verifier and not auth_header:
            ctx.response.status_code = 401
            ctx.response.body = '{"error": "Unauthorized"}'
            ctx.response.headers["Content-Type"] = "application/json"
            return False
        return True
