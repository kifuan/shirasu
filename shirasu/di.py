import inspect
from typing import Any, Callable, Awaitable, TypeVar, Literal, overload
from .logger import logger


T = TypeVar('T')


class DependencyError(Exception):
    """
    Base error for dependency injection errors.
    """

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
    """
    Duplicate provider.
    """

    def __init__(self, dep: str) -> None:
        super().__init__([dep], 'duplicate dependency provider')


class DependencyInjector:
    """
    Dependency injector based on annotations.
    Note: it does not support positional-only arguments.
    """

    def __init__(self) -> None:
        self._providers: dict[str, Callable[..., Awaitable[T]]] = {}

    async def _inject_func_args(self, func: Callable[..., Awaitable[Any]], *inject_for: str) -> dict[str, Any]:
        params = inspect.signature(func).parameters

        # Check unknown dependencies.
        if unknown_deps := [dep for dep in params if dep not in self._providers]:
            raise UnknownDependencyError(unknown_deps)

        # Check circular dependencies.
        if circular_deps := [dep for dep in params if dep in inject_for]:
            raise CircularDependencyError(circular_deps)

        args = {
            dep: await self._apply(self._providers[dep], dep, *inject_for)
            for dep in params
        }

        # Check types of injected parameters.
        for dep, param in params.items():
            if not isinstance(val := args[dep], expected := param.annotation):
                module = inspect.getmodule(func)
                module_name = module.__name__ if module else '<unknown module>'
                module_func_name = f'{module_name}:{func.__name__}'
                logger.warning(f'type mismatch for parameter {dep} in function {module_func_name}, '
                               f'real type: {type(val).__name__}, expected: {expected.__name__}')

        return args

    async def _apply(self, func: Callable[..., Any], *apply_for: str) -> Any:
        injected_args = await self._inject_func_args(func, *apply_for)
        if inspect.iscoroutine(result := func(**injected_args)):
            result = await result
        return result

    @overload
    def inject(
            self,
            func: Callable[..., Awaitable[T]],
            *,
            sync: Literal[False] = False,
    ) -> Callable[[], Awaitable[T]]:
        """
        Injects async function.
        :param func: the async function to inject.
        :param sync: the mark.
        :return: the injected function.
        """

    @overload
    def inject(
            self,
            func: Callable[..., T],
            *,
            sync: Literal[True],
    ) -> Callable[[], Awaitable[T]]:
        """
        Injects sync function.
        :param func: the sync function to inject.
        :param sync: the mark.
        :return: the injected function.
        """

    def inject(
            self,
            func: Callable[..., Any],
            *,
            sync: bool = False
    ) -> Callable[[], Any]:
        if not sync:
            assert inspect.iscoroutinefunction(func), 'you lied.'

        async def wrapper():
            return await self._apply(func)
        return wrapper

    @overload
    def provide(
            self,
            name: str,
            func: Callable[..., Awaitable[T]],
            *,
            sync: Literal[False] = False,
            check_duplicate: bool = True
    ) -> None: ...

    @overload
    def provide(
            self,
            name: str,
            func: Callable[..., T],
            *,
            sync: Literal[True],
            check_duplicate: bool = True
    ) -> None: ...

    def provide(
            self,
            name: str,
            func: Callable[..., Any],
            *,
            sync: bool = False,
            check_duplicate: bool = True
    ) -> None:
        if not sync:
            assert inspect.iscoroutinefunction(func), 'you lied.'

        if check_duplicate and name in self._providers:
            raise DuplicateDependencyProviderError(name)

        self._providers[name] = func


di = DependencyInjector()
"""
The global dependency injector.
"""


@overload
def inject(*, sync: Literal[False] = False) -> Callable[[Callable[..., Awaitable[T]]], Callable[[], Awaitable[T]]]: ...


@overload
def inject(*, sync: Literal[True]) -> Callable[[Callable[..., T]], Callable[[], Awaitable[T]]]: ...


def inject(*, sync: bool = False) -> Any:
    """
    Injects function using decorator.
    :return: the decorator to inject function.
    """

    def deco(func: Callable[..., Awaitable[T]]) -> Callable[[], Awaitable[T]]:
        return di.inject(func, sync=sync)  # type: ignore
    return deco


@overload
def provide(
        name: str,
        *,
        sync: Literal[False] = False,
        check_duplicate: bool = True,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]: ...


@overload
def provide(
        name: str,
        *,
        sync: Literal[True],
        check_duplicate: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., Awaitable[T]]]: ...


def provide(name: str, *, sync: bool = False, check_duplicate: bool = True) -> Any:
    """
    Registers provider using decorator.
    :return: the decorator to register provider.
    """

    def deco(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        di.provide(name, func, sync=sync, check_duplicate=check_duplicate)  # type: ignore
        return func
    return deco
