import inspect
from typing import Any, Callable, Awaitable, TypeVar


_T = TypeVar('_T')


class DependencyError(Exception):
    def __init__(self, deps: list[type], prompt: str) -> None:
        super().__init__(f'{prompt}: {", ".join(d.__name__ for d in deps)}')
        self.deps = deps


class UnknownDependencyError(DependencyError):
    """
    Dependency not found.
    """

    def __init__(self, deps: list[type]) -> None:
        super().__init__(deps, 'unknown dependencies')


class CircularDependencyError(DependencyError):
    """
    Circular dependency.
    """

    def __init__(self, deps: list[type]) -> None:
        super().__init__(deps, 'circular dependencies')


class DuplicateDependencyProviderError(DependencyError):
    def __init__(self, dep: type) -> None:
        super().__init__([dep], 'duplicate dependency provider')


class DependencyInjector:
    """
    Dependency injector based on annotations.
    Note: it does not support positional-only arguments.
    """

    def __init__(self) -> None:
        self._providers: dict[type, Callable[..., Awaitable[Any]]] = {}

    async def _inject_func_args(self, func: Callable[..., Awaitable[Any]], *inject_for: type) -> dict[str, Any]:
        params = {
            name: param.annotation
            for name, param in inspect.signature(func).parameters.items()
        }

        if unknown_deps := [typ for typ in params.values() if typ not in self._providers]:
            raise UnknownDependencyError(unknown_deps)

        if circular_deps := [typ for typ in params.values() if typ in inject_for]:
            raise CircularDependencyError(circular_deps)

        return {
            name: await self._apply(self._providers[typ], typ, *inject_for)
            for name, typ in params.items()
        }

    async def _apply(self, func: Callable[..., Awaitable[_T]], *apply_for: type) -> _T:
        injected_args = await self._inject_func_args(func, *apply_for)
        return await func(**injected_args)

    def inject(self, func: Callable[..., Awaitable[_T]]) -> Callable[[], Awaitable[_T]]:
        assert inspect.iscoroutinefunction(func), 'Injected function must be async.'

        async def wrapper():
            return await self._apply(func)
        return wrapper

    def provide(self, func: Callable[..., Awaitable[_T]], *, check_duplicate: bool = True) -> None:
        assert inspect.iscoroutinefunction(func), 'Dependency provider must be async.'

        typ = inspect.signature(func).return_annotation
        assert typ is not None and typ != inspect.Parameter.empty, 'Dependency provider must have return type.'

        if check_duplicate and typ in self._providers:
            raise DuplicateDependencyProviderError(typ)

        self._providers[typ] = func


di = DependencyInjector()
"""
The global dependency injector.
"""


def inject():
    """
    Injects function using decorator.
    :return: the decorator to inject function.
    """

    def deco(func: Callable[..., Awaitable[_T]]) -> Callable[[], Awaitable[_T]]:
        return di.inject(func)
    return deco


def provide(*, check_duplicate: bool = True) -> Callable[[Callable[..., Awaitable[_T]]], Callable[..., Awaitable[_T]]]:
    """
    Registers provider using decorator.
    :return: the decorator to register provider.
    """

    def deco(func: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]:
        di.provide(func, check_duplicate=check_duplicate)
        return func
    return deco
