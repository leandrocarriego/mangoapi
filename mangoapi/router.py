# mangoapi/router.py
import datetime
import inspect
import traceback
from types import CoroutineType
from typing import Any, get_origin, get_args

from django.db.models import Model as DjangoModel, QuerySet
from django.http import Http404
from pydantic import BaseModel as PydanticModel, ValidationError
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request

from mangoapi.logging import setup_logger
from mangoapi.utils import parse_args, call_view


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

    def post(self, path, status_code=200):
        def decorator(func):
            full_path = f"{self.prefix}/{path.lstrip('/')}".rstrip("/")
            func.__status_code__ = status_code
            self.routes.append((full_path, "POST", func))
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
                serialized_result = cls._serialize_result(result, return_annotation)

                return JSONResponse(
                    serialized_result,
                    status_code=getattr(func, "__status_code__", 200),
                )

            except Http404 as e:
                return JSONResponse({"error": str(e)}, status_code=404)

            except ValidationError as e:
                logger.error("[ValidationError] Return value does not match annotation:")
                for err in e.errors():
                    logger.error(f" - {err['loc']}: {err['msg']}")
                return JSONResponse({"errors": e.errors()}, status_code=422)

            except TypeError as e:
                logger.error("[TypeError] Return value does not match annotation:")
                logger.error(f" - {str(e)}")
                return JSONResponse({"error": str(e)}, status_code=422)

            except Exception as e:
                logger.error(
                    "Unhandled exception in endpoint '%s': %s\n%s",
                    func.__name__,
                    str(e),
                    traceback.format_exc(),
                )
                return JSONResponse(
                    {"error": "Internal Server Error", "details": str(e)},
                    status_code=500,
                )

        return endpoint

    @classmethod
    def _serialize_result(cls, result: Any, return_annotation: Any) -> Any:
        """
        Serializes the result according to the declared return annotation.

        - Supports lists and individual instances of Pydantic models and Django models.
        - Falls back to returning raw data if no rule matches.
        """

        origin = get_origin(return_annotation)
        args = get_args(return_annotation)

        is_list = origin is list and args
        model_type = args[0] if is_list else None
        type_is_class = isinstance(model_type, type)

        # Case: list[PydanticModel or DjangoModel]
        is_list_of_models = (
            is_list
            and type_is_class
            and (
                issubclass(model_type, PydanticModel)
                or issubclass(model_type, DjangoModel)
            )
        )
        if is_list_of_models:
            return [
                cls._serialize_model(model, expected_type=model_type)
                for model in result
            ]

        # Case: Django QuerySet
        is_django_queryset = isinstance(result, QuerySet)
        if is_django_queryset:
            inferred_type = model_type if model_type else result.model
            return [
                cls._serialize_model(model, expected_type=inferred_type)
                for model in result
            ]

        # Case: single Pydantic model or Django model
        return cls._serialize_model(model=result, expected_type=return_annotation)

    @classmethod
    def _serialize_model(
        cls,
        model: PydanticModel | DjangoModel,
        expected_type: PydanticModel | DjangoModel,
    ) -> dict[int | str, Any]:

        type_is_class = isinstance(expected_type, type)
        if not type_is_class:
            raise TypeError(f"Expected a type, got {type(expected_type).__name__}")

        expects_pydantic_model = issubclass(expected_type, PydanticModel)
        if expects_pydantic_model:
            model_is_pydantic = isinstance(model, PydanticModel) or isinstance(model, dict)
            if not model_is_pydantic:
                raise TypeError(
                    f"Expected a Pydantic model of type {expected_type.__name__}, got {type(model).__name__}"
                )
            # This will raise ValidationError if fields are missing
            return expected_type.model_validate(model).model_dump(mode="json")

        expects_django_model = issubclass(expected_type, DjangoModel)
        if expects_django_model:
            model_is_django = isinstance(model, DjangoModel)
            if not model_is_django:
                raise TypeError(
                    f"Expected a Django model of type {expected_type.__name__}, got {type(model).__name__}"
                )
            return cls._serialize_django_model(model)

        return model

    @staticmethod
    def _serialize_django_model(obj: DjangoModel) -> dict:
        data = {}
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if isinstance(value, (datetime.datetime, datetime.date)):
                value = value.isoformat()
            data[field.name] = value
        return data
