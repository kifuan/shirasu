import pytest
from typing import Any
from shirasu.di import (
    DependencyInjector,
    CircularDependencyError,
    UnknownDependencyError,
    DuplicateDependencyProviderError,
)


NAME = 'Taffy'
YEAR = 1883


async def provide_name(year: int) -> str:
    assert year == YEAR
    return NAME


async def provide_year() -> int:
    return YEAR


async def provide_year_circular(name: str) -> int:
    pytest.fail(f'Failed because name {name} is circular.')
    return YEAR


async def provide_year_unknown(unknown_var: Any) -> int:
    pytest.fail(f'Failed because unknown var {unknown_var} should not be injected')
    return YEAR


async def user(year: int, name: str) -> None:
    assert year == YEAR
    assert name == NAME


@pytest.mark.asyncio
async def test_di():
    di = DependencyInjector()
    di.provide('name', provide_name)
    di.provide('year', provide_year)
    await di.inject(user)()


@pytest.mark.asyncio
async def test_circular():
    di = DependencyInjector()
    di.provide('name', provide_name)
    di.provide('year', provide_year_circular)
    with pytest.raises(CircularDependencyError):
        await di.inject(user)()


@pytest.mark.asyncio
async def test_unknown():
    di = DependencyInjector()
    di.provide('name', provide_name)
    di.provide('year', provide_year_unknown)
    with pytest.raises(UnknownDependencyError):
        await di.inject(user)()


def test_duplicate_provider():
    di = DependencyInjector()
    di.provide('name', provide_name)
    di.provide('name', provide_name, check_duplicate=False)
    with pytest.raises(DuplicateDependencyProviderError):
        di.provide('name', provide_name)
