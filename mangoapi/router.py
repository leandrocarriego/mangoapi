# mangoapi/router.py
import inspect

from pydantic import BaseModel, ValidationError
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request

from mangoapi.router import Router
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

    def include_router(self, router: Router) -> None:
        for path, method, func in router.routes:
            self.routes.append((path, method, func))

    def to_starlette_routes(self):
        def make_endpoint(func):
            async def endpoint(request: Request):
                try:
                    kwargs = await parse_args(func, request)
                except ValidationError as e:
                    return JSONResponse({"errors": e.errors()}, status_code=422)
                
                result = await call_view(func, **kwargs)

                # Validate return type if it is a BaseModel
                return_annotation = inspect.signature(func).return_annotation
                if inspect.isclass(return_annotation) and issubclass(return_annotation, BaseModel):
                    try:
                        validated = return_annotation(**result)
                        result = validated.model_dump()
                    except ValidationError as e:
                        return JSONResponse({"errors": e.errors()}, status_code=500)
                    
                return JSONResponse(result, status_code=getattr(func, "__status_code__", 200))

            return endpoint

        return [
            Route(path, endpoint=make_endpoint(func), methods=[method])
            for path, method, func in self.routes
        ]
