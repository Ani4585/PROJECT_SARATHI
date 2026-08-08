import inspect
import json
from typing import List, Callable, Optional
from .models import GatewayRequest, GatewayResponse, GatewayContext, GatewayRoute
from .interceptors import GatewayInterceptor

class GatewayRouter:
    def __init__(self):
        self.routes: List[GatewayRoute] = []
        self.interceptors: List[GatewayInterceptor] = []

    def add_route(self, path: str, methods: List[str], handler: Callable, name: str = ""):
        route = GatewayRoute(path, methods, handler, name)
        self.routes.append(route)

    def add_interceptor(self, interceptor: GatewayInterceptor):
        self.interceptors.append(interceptor)

    async def dispatch(self, request: GatewayRequest) -> GatewayResponse:
        ctx = GatewayContext(request)

        for interceptor in self.interceptors:
            cont = await interceptor.pre_handle(ctx)
            if not cont:
                return ctx.response

        matched_route = None
        matched_params = {}
        for route in self.routes:
            params = route.match(request.path, request.method)
            if params is not None:
                matched_route = route
                matched_params = params
                break

        if not matched_route:
            ctx.response.status_code = 404
            ctx.response.body = json.dumps({"error": "Route Not Found"})
            ctx.response.headers["Content-Type"] = "application/json"
        else:
            try:
                handler = matched_route.handler
                if inspect.iscoroutinefunction(handler):
                    res = await handler(ctx, **matched_params)
                else:
                    res = handler(ctx, **matched_params)
                if isinstance(res, GatewayResponse):
                    ctx.response = res
            except Exception as e:
                ctx.response.status_code = 500
                ctx.response.body = json.dumps({"error": "Internal Server Error", "message": str(e)})
                ctx.response.headers["Content-Type"] = "application/json"

        for interceptor in reversed(self.interceptors):
            await interceptor.post_handle(ctx)

        return ctx.response
