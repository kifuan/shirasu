import functools
from typing import TypeVar, Awaitable, Callable, ParamSpec, Any

T = TypeVar('T')
P = ParamSpec('P')


def asyncify(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)
    return wrapper
