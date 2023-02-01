import importlib
from typing import Iterator

from .addon import Addon
from ..logger import logger
from .exceptions import (
    NoSuchAddonError,
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

    def load(self, addon: Addon) -> None:
        """
        Loads addon.
        :param addon: the addons to load.
        """

        if addon.name in self._addons:
            raise DuplicateAddonError(addon.name)

        self._addons[addon.name] = addon
        logger.success(f'Loaded addon {addon.name}.')

    def load_module(self, module_name: str) -> None:
        """
        Loads addons from module.
        :param module_name: the module name.
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

    def get_addon(self, name: str) -> Addon:
        """
        Gets the addon by its name.
        If the name is not in the pool, it will raise `NoSuchAddonError`.
        :param name: the name of the addon.
        :return: the addon.
        """

        if addon := self._addons.get(name):
            return addon
        raise NoSuchAddonError(name)

    def __iter__(self) -> Iterator[Addon]:
        yield from self._addons.values()
