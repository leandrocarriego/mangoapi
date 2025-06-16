# mangoapi/utils.py
import inspect

from starlette.requests import Request
from starlette.responses import JSONResponse
from pydantic import BaseModel, ValidationError


async def parse_args(func, request: Request):
    """
    ES: Extrae los argumentos para la función `func` desde el request ASGI,
    soportando query params, body JSON y form data según el método HTTP.

    IN: Extracts arguments for the function `func` from the ASGI request,
    supporting query parameters, JSON body, and form data depending on the HTTP method.
    """
    sig = inspect.signature(func)
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

    for name, param in sig.parameters.items():
        if name == "request":
            kwargs[name] = request
        elif inspect.isclass(param.annotation) and issubclass(param.annotation, BaseModel):
            kwargs[name] = param.annotation(**body_data)
        else:
            val = request.query_params.get(name)
            if val is not None:
                kwargs[name] = val
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
