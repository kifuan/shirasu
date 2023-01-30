import asyncio
from typing import Type, Callable, Any
from functools import wraps
from ..logger import logger_deco


def retry(*, timeout: float, messages: dict[Type[BaseException], str]) -> Callable[[Any], Any]:
    def wrapper(f: Any) -> Any:
        @wraps(f)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            while True:
                try:
                    return await f(*args, **kwargs)
                except BaseException as e:
                    if not (msg := messages.get(e.__class__)):
                        raise

                    logger_deco(f).warning(f'{msg}, retrying in {timeout} seconds.', from_decorator=True)
                    await asyncio.sleep(timeout)
        return inner

    return wrapper
