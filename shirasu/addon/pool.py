import importlib
from typing import Iterator

from .addon import Addon
from ..logger import logger
from .exceptions import (
    LoadAddonError,
    DuplicateAddonError,
)


class AddonPool:
    """
    The addon pool to load and get addons.
    """

    def __init__(self) -> None:
        """
        Initializes the addon pool.
        """

        self._addons: dict[str, Addon] = {}

    @classmethod
    def from_modules(cls, *modules: str) -> 'AddonPool':
        """
        Creates a pool from addon modules.
        :param modules: the addon modules to load.
        :return: the pool.
        """

        pool = cls()
        for module in modules:
            pool.load_module(module)
        return pool

    def load(self, addon: Addon) -> 'AddonPool':
        """
        Loads addon.
        :param addon: the addons to load.
        :return: the pool itself to chain function calls.
        """

        if addon.name in self._addons:
            raise DuplicateAddonError(addon.name)

        self._addons[addon.name] = addon
        logger.success(f'Loaded addon {addon.name}.')
        return self

    def load_module(self, module_name: str) -> 'AddonPool':
        """
        Loads addons from module.
        :param module_name: the module name.
        :return: the pool itself to chain function calls.
        """

        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise LoadAddonError(f'failed to load addons in module {module_name}') from e

        addons = [p for p in module.__dict__.values() if isinstance(p, Addon)]
        if not addons:
            raise LoadAddonError(f'no addons in module {module_name}')

        for addon in addons:
            self.load(addon)

        return self

    def get_addon(self, name: str) -> Addon | None:
        """
        Gets the addon by its name, or None if the addon is absent.
        :param name: the name of the addon.
        :return: the addon.
        """

        return self._addons.get(name)

    def __iter__(self) -> Iterator[Addon]:
        yield from self._addons.values()
