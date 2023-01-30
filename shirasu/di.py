import inspect
from typing import Any, Callable, Awaitable, TypeVar


_T = TypeVar('_T')


class DependencyError(Exception):
    def __init__(self, deps: list[str], prompt: str) -> None:
        super().__init__(f'{prompt}: {", ".join(deps)}')
        self.deps = deps


class UnknownDependencyError(DependencyError):
    """
    Dependency not found.
    """

    def __init__(self, deps: list[str]) -> None:
        super().__init__(deps, 'unknown dependencies')


class CircularDependencyError(DependencyError):
    """
    Circular dependency.
    """

    def __init__(self, deps: list[str]) -> None:
        super().__init__(deps, 'circular dependencies')


class DuplicateDependencyProviderError(DependencyError):
    def __init__(self, dep: str) -> None:
        super().__init__([dep], 'duplicate dependency provider')


class DependencyInjector:
    """
    Dependency injector based on annotations.
    Note: it does not support positional-only arguments.
    """

    def __init__(self) -> None:
        self._providers: dict[str, Callable[..., Awaitable[Any]]] = {}

    async def _inject_func_args(self, func: Callable[..., Awaitable[Any]], *inject_for: str) -> dict[str, Any]:
        deps = [name for name in inspect.signature(func).parameters]

        if unknown_deps := [dep for dep in deps if dep not in self._providers]:
            raise UnknownDependencyError(unknown_deps)

        if circular_deps := [dep for dep in deps if dep in inject_for]:
            raise CircularDependencyError(circular_deps)

        return {
            dep: await self._apply(self._providers[dep], dep, *inject_for)
            for dep in deps
        }

    async def _apply(self, func: Callable[..., Awaitable[_T]], *apply_for: str) -> _T:
        injected_args = await self._inject_func_args(func, *apply_for)
        return await func(**injected_args)

    def inject(self, func: Callable[..., Awaitable[_T]]) -> Callable[[], Awaitable[_T]]:
        assert inspect.iscoroutinefunction(func), 'Injected function must be async.'

        async def wrapper():
            return await self._apply(func)
        return wrapper

    def provide(self, name: str, func: Callable[..., Awaitable[_T]], *, check_duplicate: bool = True) -> None:
        assert inspect.iscoroutinefunction(func), 'Dependency provider must be async.'

        if check_duplicate and name in self._providers:
            raise DuplicateDependencyProviderError(name)

        self._providers[name] = func


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


def provide(name: str, *, check_duplicate: bool = True) -> Callable[[Callable[..., Awaitable[_T]]], Callable[..., Awaitable[_T]]]:
    """
    Registers provider using decorator.
    :return: the decorator to register provider.
    """

    def deco(func: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]:
        di.provide(name, func, check_duplicate=check_duplicate)
        return func
    return deco
