# mangoapi/router.py
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request

from mangoapi.utils import parse_args, call_view


class Router:
    def __init__(self, prefix=""):
        self.prefix = prefix.rstrip("/")
        self.routes = []

    def get(self, path, status_code=200):
        def decorator(func):
            full_path = f"{self.prefix}/{path.lstrip('/')}".rstrip("/")
            func.__status_code__ = status_code
            self.routes.append((full_path, "GET", func))
            return func

        return decorator

    def post(self, path, status_code=200):
        def decorator(func):
            full_path = f"{self.prefix}/{path.lstrip('/')}".rstrip("/")
            func.__status_code__ = status_code
            self.routes.append((full_path, "POST", func))
            return func

        return decorator

    def include_router(self, other):
        for path, method, func in other.routes:
            self.routes.append((path, method, func))

    def to_starlette_routes(self):
        def make_endpoint(func):
            async def endpoint(request: Request):
                kwargs = await parse_args(func, request)
                result = await call_view(func, **kwargs)
                return JSONResponse(
                    result, status_code=getattr(func, "__status_code__", 200)
                )

            return endpoint

        return [
            Route(path, endpoint=make_endpoint(func), methods=[method])
            for path, method, func in self.routes
        ]
