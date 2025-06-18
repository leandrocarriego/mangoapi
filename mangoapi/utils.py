# mangoapi/utils.py
import inspect

from starlette.requests import Request
from pydantic import BaseModel


async def parse_args(func, request: Request):
    """
    ES: Extrae los argumentos para la función `func` desde el request ASGI,
    incluyendo path params, query params, body JSON y form data.
    """
    signature = inspect.signature(func)
    kwargs = {}

    # Extraer body si aplica
    body_data = {}
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body_data = await request.json()
        except Exception:
            try:
                form = await request.form()
                body_data = dict(form)
            except Exception:
                body_data = {}

    for name, param in signature.parameters.items():
        if name == "request":
            kwargs[name] = request
        elif inspect.isclass(param.annotation) and issubclass(
            param.annotation, BaseModel
        ):
            kwargs[name] = param.annotation(**body_data)
        elif name in request.path_params:
            # 🟢 Soporte para path parameters
            val = request.path_params[name]
            if param.annotation != inspect._empty:
                try:
                    val = param.annotation(val)  # casteo automático si es posible
                except Exception:
                    pass
            kwargs[name] = val
        elif name in request.query_params:
            kwargs[name] = request.query_params[name]
        elif name in body_data:
            kwargs[name] = body_data[name]
        elif param.default != inspect._empty:
            kwargs[name] = param.default
        else:
            kwargs[name] = None

    return kwargs


async def call_view(func, **kwargs):
    """
    ES: Ejecuta la función `func` con los argumentos `kwargs`.
    Si `func` es una coroutine (función async), la await-ea correctamente.
    Retorna el resultado de la función.

    EN: Executes the `func` function with the `kwargs` arguments.
    If `func` is a coroutine (async function), it awaits it properly.
    Returns the function's result.
    """
    return await func(**kwargs)


def is_type(tp: type) -> bool:
    return isinstance(tp, type)
