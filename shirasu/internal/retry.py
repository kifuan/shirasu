import asyncio
from typing import Type, Callable, Any
from functools import wraps
from ..logger import logger, logger_with_func_name


def retry(
        *,
        timeout: float,
        skip: Type[BaseException],
        messages: dict[Type[BaseException], str]
) -> Callable[[Any], Any]:
    # I don't think this should be annotated exactly.

    def wrapper(f: Any) -> Any:
        @wraps(f)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            while True:
                try:
                    return await f(*args, **kwargs)
                except BaseException as e:
                    if e.__class__ == skip:
                        return

                    if not (msg := messages.get(e.__class__)):
                        raise

                    logger_with_func_name(
                        name=f.__name__,
                    ).warning(f'{msg}, retrying in {timeout} seconds.', from_decorator=True)
                    await asyncio.sleep(timeout)
        return inner

    return wrapper
