# mangoapi/utils.py
import inspect

from starlette.requests import Request


async def parse_args(func, request: Request):
    """
    ES: Extrae los argumentos para la función `func` desde el request ASGI,
    soportando query params, body JSON y form data según el método HTTP.

    IN: Extracts arguments for the function `func` from the ASGI request,
    supporting query parameters, JSON body, and form data depending on the HTTP method.
    """
    sig = inspect.signature(func)
    kwargs = {}

    # Query params siempre están disponibles
    # Query params are always available
    query_params = request.query_params
    print("DEBUG query_params:", dict(query_params))

    # Para métodos que pueden llevar body, parseamos JSON o form
    # For methods that can carry a body, parse JSON or form data
    body = {}
    if request.method in ("POST", "PUT", "PATCH"):
        # Intentamos leer JSON
        # Try to read JSON body
        try:
            body = await request.json()
        except Exception:
            # Si no es JSON, intentamos form data
            # If not JSON, try form data
            try:
                form = await request.form()
                body = dict(form)
            except Exception:
                body = {}

    for name, param in sig.parameters.items():
        if name == "request":
            kwargs[name] = request
        else:
            val = query_params.get(name, None)
            if val is not None:
                kwargs[name] = val
            elif body and name in body:
                kwargs[name] = body[name]
            else:
                kwargs[name] = (
                    param.default if param.default != inspect._empty else None
                )

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
