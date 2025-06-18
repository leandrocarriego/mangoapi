# mangoapi/validators.py
from typing import get_origin, get_args, Union, TypeAlias
from django.db.models import Model as DjangoModel, QuerySet as DjangoQuerySet
from pydantic import BaseModel as PydanticModel, ValidationError

from mangoapi.exceptions import ValidationTypeError
from mangoapi.logging import setup_logger


PrimitiveType: TypeAlias = str | int | float | bool | dict
ModelType: TypeAlias = type[PydanticModel] | type[DjangoModel]
ReturnType: TypeAlias = (
    ModelType
    | type[DjangoQuerySet]
    | list[ModelType | PrimitiveType]
    | dict[str | int | float, PrimitiveType]
)


PRIMITIVE_TYPES = (str, int, float, bool, dict)

logger = setup_logger()


def validate_return_type(result: object, return_annotation: ReturnType) -> bool:
    origin = get_origin(return_annotation)
    args = get_args(return_annotation)

    try:
        # list[None] or dict[None, None]
        is_empty_list_or_dict = not args and origin in (list, dict)
        if is_empty_list_or_dict:
            return _validate_empty_list_or_dict(result)

        # list[X]
        is_list = origin is list and args
        if is_list:
            return _validate_list(result, args)

        # dict[str, X]
        is_dict = origin is dict and len(args) == 2
        if is_dict:
            return _validate_dict(result, args)

        return _validate_single_model(result, return_annotation)

    except ValidationError as e:
        logger.error("[ValidationError] Return value does not match annotation:")
        for err in e.errors():
            logger.error(f" - {err['loc']}: {err['msg']}")
        raise ValidationTypeError()

    except Exception as e:
        logger.exception(
            "[ValidationTypeError] Unexpected error while validating return type"
        )
        raise ValidationTypeError(str(e))


def _validate_empty_list_or_dict(result) -> bool:
    return isinstance(result, (list, dict)) and len(result) == 0


def _validate_list(result, args) -> bool:
    item_type = args[0]

    if not isinstance(result, (list, DjangoQuerySet)):
        return False

    return _check_and_validate(item_type, result)


def _validate_dict(result, args) -> bool:
    _, value_type = args

    if not isinstance(result, dict):
        return False

    dataset = [v for _, v in result.items()]

    return _check_and_validate(value_type, dataset)


def _check_and_validate(item_type, dataset) -> bool:
    if _is_union_type(item_type):
        return all(_validate_union_item(item, item_type) for item in dataset)

    if _is_primitive(item_type):
        return all(_validate_primitive(item, item_type) for item in dataset)

    return all(_validate_single_model(item, item_type) for item in dataset)


def _validate_union_item(item: object, expected_union: type) -> bool:
    for expected in get_args(expected_union):
        if _validate_primitive(item, expected):
            return True
        if _validate_single_model(item, expected):
            return True
    return False


def _validate_primitive(item: object, expected_type: type) -> bool:
    return expected_type in PRIMITIVE_TYPES and isinstance(item, expected_type)


def _validate_single_model(model: object, expected_type: ReturnType) -> bool:
    if not isinstance(expected_type, type):
        return False

    expected_pydantic_model = issubclass(expected_type, PydanticModel)
    if expected_pydantic_model:
        try:
            expected_type.model_validate(model)
            return True
        except ValidationError:
            return False

    expected_django_model = issubclass(expected_type, DjangoModel)
    if expected_django_model:
        return isinstance(model, expected_type)

    return False


def _is_union_type(tp: type) -> bool:
    return get_origin(tp) is Union


def _is_primitive(tp: type) -> bool:
    return tp in PRIMITIVE_TYPES
