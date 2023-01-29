import asyncio
from typing import Type, Callable, Any
from functools import wraps
from ..logger import logger


def retry(
        *,
        timeout: float,
        skip: Type[BaseException],
        messages: dict[Type[BaseException], str]
) -> Callable[[Any], Any]:
    # I don't think this should be annotated exactly.

    def wrapper(f: Any) -> Any:
        @wraps(f)
        async def inner(*args, **kwargs):
            while True:
                try:
                    await f(*args, **kwargs)
                except BaseException as e:
                    if e.__class__ == skip:
                        return

                    if not (msg := messages.get(e.__class__)):
                        raise

                    logger.warning(f'{msg}, retrying in {timeout} seconds.')
                    await asyncio.sleep(timeout)
        return inner

    return wrapper
