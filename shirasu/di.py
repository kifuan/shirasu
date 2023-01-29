import inspect
from typing import Any, Callable, Awaitable, TypeVar
from .logger import logger
from .internal import SingletonMeta


_T = TypeVar('_T')


class UnknownDependencyError(Exception):
    """
    Dependency not found.
    """

    def __init__(self, deps: list[type]) -> None:
        names = ', '.join(d.__name__ for d in deps)
        super().__init__(f'unknown dependencies: {names}')
        self.deps = deps


class DependencyInjector(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._dependencies: dict[type, Callable[[...], Awaitable[Any]]] = {}

    async def _inject_func_args(self, func: Callable[[...], Awaitable[Any]]) -> dict[str, Any]:
        params = inspect.signature(func).parameters

        # Use := operator here is too ugly.
        unknown_deps = [
            param.annotation for param in params.values()
            if param.annotation not in self._dependencies
        ]

        if unknown_deps:
            raise UnknownDependencyError(unknown_deps)

        return {
            name: await self._apply(self._dependencies[param.annotation])
            for name, param in params.items()
        }

    async def _apply(self, func: Callable[[...], Awaitable[_T]]) -> _T:
        injected_args = await self._inject_func_args(func)
        return await func(**injected_args)

    def inject(self, func: Callable[[...], Awaitable[_T]]) -> Callable[[], Awaitable[_T]]:
        assert inspect.iscoroutinefunction(func), 'Injected function must be async.'

        async def wrapper():
            return await self._apply(func)
        return wrapper

    def provide(self, typ: type, func: Callable[[...], Awaitable[_T]]) -> None:
        assert inspect.iscoroutinefunction(func), 'Dependency provider must be async.'

        if typ in self._dependencies:
            logger.warning(f'Dependency provider of {typ.__name__} will be overwritten.')

        self._dependencies[typ] = func


def inject():
    def deco(func: Callable[[...], Awaitable[_T]]) -> Callable[[], Awaitable[_T]]:
        return DependencyInjector().inject(func)
    return deco


def provide(typ: type) -> Callable[[_T], _T]:
    def deco(func: _T) -> _T:
        DependencyInjector().provide(typ, func)
        return func
    return deco
