# mangoapi/serializer.py
import datetime
from typing import TypeAlias, get_origin, get_args

from django.db.models import Model as DjangoModel, QuerySet
from pydantic import BaseModel as PydanticModel

from mangoapi.exceptions import SerializationError
from mangoapi.logging import setup_logger
from mangoapi.utils import is_type

logger = setup_logger()

PRIMITIVE_TYPES = (str, int, float, bool, dict)

ModelInstance: TypeAlias = DjangoModel | PydanticModel
ResultToSerialize: TypeAlias = list[ModelInstance] | QuerySet | ModelInstance
ExpectedReturnType: TypeAlias = type[DjangoModel] | type[PydanticModel] | list | dict
SerializedDict: TypeAlias = dict[str, int | float | str | bool | None | list | dict]


def serialize_result(
    result: ResultToSerialize, return_annotation: ExpectedReturnType
) -> SerializedDict | list[SerializedDict | None]:
    origin = get_origin(return_annotation)
    args = get_args(return_annotation)

    if origin in [dict, list] and not args:
        return {} if origin is dict else []

    try:
        is_list_with_args = origin is list and args
        model_type = args[0] if is_list_with_args else None
        type_is_class = isinstance(model_type, type)

        if is_list_with_args and type_is_class:
            # Case: list[PydanticModel or DjangoModel]
            is_list_of_models = issubclass(model_type, PydanticModel) or issubclass(
                model_type, DjangoModel
            )
            if is_list_of_models:
                return [
                    _serialize_model(model, expected_type=model_type)
                    for model in result
                ]

            # Case: list[primitive]
            is_list_of_primitives = model_type in PRIMITIVE_TYPES
            if is_list_of_primitives:
                return result
        
        # Case: dict[primitive, primitive]
        if isinstance(result, dict) and origin is dict:
            return result

        # Case: Django QuerySet
        is_django_queryset = isinstance(result, QuerySet)
        if is_django_queryset:
            inferred_type = model_type if model_type else result.model
            return [
                _serialize_model(model, expected_type=inferred_type) for model in result
            ]

        # Case: single Pydantic model or Django model
        return _serialize_model(model=result, expected_type=return_annotation)

    except Exception as e:
        logger.exception(f"[SerializationError] Failed to serialize: {e}")
        logger.error(f" - {str(e)}")
        raise SerializationError()


def _serialize_model(
    model: PydanticModel | DjangoModel, expected_type: ExpectedReturnType
) -> SerializedDict:
    type_name = getattr(expected_type, '__name__', repr(expected_type))
    if not is_type(expected_type):
        raise TypeError(
            f"Expected a class type for serialization, got: {type_name}"
        )

    expects_pydantic_model = issubclass(expected_type, PydanticModel)
    if expects_pydantic_model:
        return _serialize_pydantic_model(model, expected_type)

    expects_django_model = issubclass(expected_type, DjangoModel)
    if expects_django_model:
        return _serialize_django_model(model)

    raise TypeError(f"Invalid type for serialization: {type_name}")


def _serialize_pydantic_model(model: PydanticModel | dict, expected_type: type[PydanticModel]) -> SerializedDict:
    if isinstance(model, dict):
        model = expected_type.model_validate(model)

    # This will raise ValidationError if fields are missing
    return model.model_dump(mode="json")


def _serialize_django_model(model: DjangoModel) -> SerializedDict:
    data = {}
    for field in model._meta.fields:
        value = getattr(model, field.name)
        if isinstance(value, (datetime.datetime, datetime.date)):
            value = value.isoformat()
        data[field.name] = value

    return data
