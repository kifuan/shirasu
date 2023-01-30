import importlib
from typing import Iterator

from .addon import Addon
from ..logger import logger
from ..util import SingletonMeta


class AddonPool(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._addons: dict[str, Addon] = {}

    def load(self, addon: Addon, namespace: str | None = None) -> None:
        """
        Loads addon.
        :param addon: the addons to load.
        :param namespace: the namespace in config file.
        """

        if namespace is None:
            namespace = addon.name

        if namespace in self._addons:
            logger.warning(f'Duplicate namespace {namespace}, skipping.')
            return

        if addon in self._addons.values():
            logger.warning(f'Duplicate addon {addon.name}, skipping.')
            return

        self._addons[namespace] = addon
        logger.success(f'Loaded addon {addon.name} with namespace {namespace}.')

    def load_module(self, module_name: str, namespace: str | None = None) -> None:
        """
        Loads addons from module.
        :param module_name: the module name.
        :param namespace: the namespace in config file.
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

        self.load(addon, namespace)

    def get_namespace(self, addon: Addon) -> str:
        for namespace, add in self._addons.items():
            if add is addon:
                return namespace
        raise NameError(f'no namespace for addon {addon.name}')

    def get_addon(self, namespace: str) -> Addon:
        if addon := self.get_addon(namespace):
            return addon
        raise NameError(f'no addon for namespace {namespace}')

    def __iter__(self) -> Iterator[Addon]:
        yield from self._addons.values()
