import importlib
from typing import Iterator

from .addon import Addon
from ..logger import logger


class AddonPool:
    def __init__(self) -> None:
        self._addons: dict[str, Addon] = {}

    def load(self, addon: Addon) -> None:
        """
        Loads addon.
        :param addon: the addons to load.
        """

        if addon.name in self._addons:
            logger.warning(f'Duplicate addon name {addon.name}, skipping.')
            return

        self._addons[addon.name] = addon
        logger.success(f'Loaded addon {addon.name}.')

    def load_module(self, module_name: str) -> None:
        """
        Loads addons from module.
        :param module_name: the module name.
        """

        if module_name in self._addons:
            logger.warning(f'Attempted to load duplicate module {module_name}.')
            return

        try:
            module = importlib.import_module(module_name)
        except ImportError:
            logger.error(f'Failed to load module {module_name}.')
            return

        addons = [p for p in module.__dict__.values() if isinstance(p, Addon)]
        if not addons:
            logger.warning(f'No addons in module {module_name}, skipping.')
            return

        addon = addons[0]

        if len(addons) > 1:
            logger.warning(f'Too many addons in single module {module_name}, load {addon.name} only.')

        self.load(addon)

    def get_addon(self, name: str) -> Addon:
        if addon := self.get_addon(name):
            return addon
        raise NameError(f'no addon for namespace {name}')

    def __iter__(self) -> Iterator[Addon]:
        yield from self._addons.values()
