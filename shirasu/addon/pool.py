import importlib
from typing import Iterator
from itertools import chain

from .addon import Addon
from ..logger import logger
from ..internal import SingletonMeta


DEFAULT_ADDON_MODULE_NAME = '@DEFAULT'


class AddonPool(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._addons: dict[str, list[Addon]] = {}

    def load(self, *addons: Addon, module: str = DEFAULT_ADDON_MODULE_NAME) -> None:
        """
        Loads addons. Just omit `module` when applying this method manually.
        :param addons: the addons to load.
        :param module: the module name.
        """

        self._addons.setdefault(module, [])

        for addon in addons:
            self._addons[module].append(addon)
            logger.success(f'Loaded addon {addon.name} from module {module}.')

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

        self.load(*addons, module=module_name)

    def __iter__(self) -> Iterator[Addon]:
        yield from chain.from_iterable(self._addons.values())
