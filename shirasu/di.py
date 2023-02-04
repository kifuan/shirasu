import asyncio
import inspect
from typing import cast, Any, Callable, Awaitable, TypeVar, ParamSpec
from .logger import logger


T = TypeVar('T')
P = ParamSpec('P')


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
    Dependency injector based on parameter names.
    Note: positional-only arguments are not supported.
    """

    def __init__(self) -> None:
        self._providers: dict[str, Callable[..., Awaitable[T]]] = {}

    async def _inject_func_args(self, func: Callable[..., Awaitable[T]], *inject_for: str) -> dict[str, Any]:
        params = inspect.signature(func).parameters

        # Check unknown dependencies.
        if unknown_deps := [dep for dep in params if dep not in self._providers]:
            raise UnknownDependencyError(unknown_deps)

        # Check circular dependencies.
        if circular_deps := [dep for dep in params if dep in inject_for]:
            raise CircularDependencyError(circular_deps)

        args = dict(zip(params, await asyncio.gather(*(
            self._apply(self._providers[dep], dep, *inject_for)
            for dep in params
        ))))

        # Check types of injected parameters.
        for dep, param in params.items():
            anno = param.annotation

            # Skip untyped parameters.
            if anno == inspect.Parameter.empty:
                continue

            if not isinstance(val := args[dep], expected := anno):
                module = inspect.getmodule(func)
                module_name = module.__name__ if module else '<unknown module>'
                module_func_name = f'{module_name}:{func.__name__}'
                logger.warning(f'type mismatch for parameter {dep} in function {module_func_name}, '
                               f'real type: {type(val).__name__}, expected: {expected.__name__}')

        return args

    async def _apply(self, func: Callable[..., Awaitable[T]], *apply_for: str) -> T:
        injected_args = await self._inject_func_args(func, *apply_for)
        return await func(**injected_args)

    def inject(self, func: Callable[..., Awaitable[T]]) -> Callable[[], Awaitable[T]]:
        """
        Injects function.
        :param func: the sync function to inject.
        :return: the injected function.
        """

        assert inspect.iscoroutinefunction(func), 'the injected function should be async'

        async def wrapper() -> T:
            return cast(T, await self._apply(func))
        return wrapper

    def provide(self, name: str, func: Callable[..., Awaitable[T]], *, check_duplicate: bool = True) -> None:
        """
        Registers provider.
        :param name: the name of the dependency it provides.
        :param func: the provider function.
        :param check_duplicate: whether to check the dependencies are duplicate.
        """

        assert inspect.iscoroutinefunction(func), 'the provider should be async'

        if check_duplicate and name in self._providers:
            raise DuplicateDependencyProviderError(name)

        self._providers[name] = func


di = DependencyInjector()
"""
The global dependency injector.
"""


def inject() -> Callable[[Callable[..., Awaitable[T]]], Callable[[], Awaitable[T]]]:
    """
    Injects given function using decorator.

    >>> @inject()
    >>> async def foo(bar: int) -> None: ...

    :return: the decorator to inject given function.
    """

    def deco(func: Callable[..., Awaitable[T]]) -> Callable[[], Awaitable[T]]:
        return di.inject(func)
    return deco


def provide(name: str, *, check_duplicate: bool = True) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Registers given provider using decorator.

    >>> @provide('foo')
    >>> async def provide_foo() -> int: ...

    :return: the decorator to register given provider.
    """

    def deco(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        di.provide(name, func, check_duplicate=check_duplicate)
        return func
    return deco
