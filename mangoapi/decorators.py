# mangoapi/decorators.py
from functools import wraps
from asgiref.sync import sync_to_async, iscoroutinefunction

def async_orm(func):
    if iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await sync_to_async(func)(*args, **kwargs)
        return wrapper
    return func
