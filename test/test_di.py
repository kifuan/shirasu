import pytest
from shirasu.di import DependencyInjector, CircularDependencyError, UnknownDependencyError


FLOAT = 12.
INT = 120


async def provide_int(_: float) -> int:
    return INT


async def provide_float_circular(_: int) -> float:
    return FLOAT


async def provide_float_unknown_dep(_: str) -> float:
    return FLOAT


async def provide_float() -> float:
    return FLOAT


async def user(i: int, f: float) -> None:
    assert i == INT and f == FLOAT


@pytest.mark.asyncio
async def test_di():
    di = DependencyInjector()
    di.provide(provide_int)
    di.provide(provide_float)
    await di.inject(user)()


@pytest.mark.asyncio
async def test_circular():
    di = DependencyInjector()
    di.provide(provide_int)
    di.provide(provide_float_circular)
    with pytest.raises(CircularDependencyError):
        await di.inject(user)()


@pytest.mark.asyncio
async def test_unknown():
    di = DependencyInjector()
    di.provide(provide_int)
    di.provide(provide_float_unknown_dep)
    with pytest.raises(UnknownDependencyError):
        await di.inject(user)()
