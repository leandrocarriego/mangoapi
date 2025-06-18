# mangoapi/router.py
import inspect
import traceback
from types import CoroutineType
from typing import Any

from django.http import Http404
from pydantic import ValidationError
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

from mangoapi.exceptions import SerializationError, ValidationTypeError
from mangoapi.logging import setup_logger
from mangoapi.serializer import serialize_result
from mangoapi.utils import parse_args, call_view
from mangoapi.validators import validate_return_type


logger = setup_logger()


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

    def post(self, path, status_code=201):
        def decorator(func):
            full_path = f"{self.prefix}/{path.lstrip('/')}".rstrip("/")
            func.__status_code__ = status_code
            self.routes.append((full_path, "POST", func))
            return func

        return decorator

    def put(self, path, status_code=200):
        def decorator(func):
            full_path = f"{self.prefix}/{path.lstrip('/')}".rstrip("/")
            func.__status_code__ = status_code
            self.routes.append((full_path, "PUT", func))
            return func

        return decorator

    def delete(self, path, status_code=204):
        def decorator(func):
            full_path = f"{self.prefix}/{path.lstrip('/')}".rstrip("/")
            func.__status_code__ = status_code
            self.routes.append((full_path, "DELETE", func))
            return func

        return decorator

    def include_router(self, router: "Router") -> None:
        for path, method, func in router.routes:
            self.routes.append((path, method, func))

    def to_starlette_routes(self):
        return [
            Route(path, endpoint=self._make_endpoint(func), methods=[method])
            for path, method, func in self.routes
        ]

    @classmethod
    def _make_endpoint(cls, func) -> CoroutineType[Any, Any, JSONResponse]:
        async def endpoint(request: Request) -> JSONResponse:
            try:
                kwargs = await parse_args(func, request)
                result = await call_view(func, **kwargs)

                # Serialization
                signature = inspect.signature(func)
                return_annotation = signature.return_annotation
                status_code = getattr(func, "__status_code__", 200)

                # Return empty response
                if status_code == 204 and return_annotation in [None, type(None)]:
                    return Response(status_code=status_code)

                if not validate_return_type(result, return_annotation):
                    raise TypeError(f"Expected {return_annotation}, got {type(result)}")

                serialized_result = serialize_result(result, return_annotation)

                return JSONResponse(serialized_result, status_code=status_code)

            except Http404 as e:
                return JSONResponse({"error": str(e)}, status_code=404)

            except (
                ValidationTypeError,
                SerializationError,
                ValidationError,
                TypeError,
            ) as e:
                return JSONResponse({"error": str(e)}, status_code=422)

            except Exception as e:
                logger.exception(
                    "Unhandled exception in endpoint '%s': %s\n%s",
                    func.__name__,
                    str(e),
                    traceback.format_exc(),
                )
                return JSONResponse({"error": "Internal Server Error"}, status_code=500)

        return endpoint
