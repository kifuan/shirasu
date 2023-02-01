import asyncio
import functools
from typing import Type, Callable, Any
from ..logger import logger_deco


def retry(*, timeout: float, messages: dict[Type[BaseException], str]) -> Callable[[Any], Any]:
    def wrapper(f: Any) -> Any:
        @functools.wraps(f)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            while True:
                try:
                    return await f(*args, **kwargs)
                except BaseException as e:
                    if not (msg := messages.get(e.__class__)):
                        raise

                    logger_deco(f).warning(f'{msg}, retrying in {timeout} seconds.')
                    await asyncio.sleep(timeout)
        return inner

    return wrapper
