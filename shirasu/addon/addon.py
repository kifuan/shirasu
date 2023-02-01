import asyncio
from typing import Callable, Awaitable, Any, Type
from pydantic import BaseModel

from .rule import Rule
from ..di import di
from ..logger import logger
from ..config import GlobalConfig


class Addon:
    """
    The addon to define addons, providing decorator `receive` to define receivers.
    Note: functions decorated by `receive` will also be injected.
    """

    def __init__(self, *, name: str, usage: str, description: str, config_model: Type[BaseModel] = BaseModel) -> None:
        """
        Initializes an addon. If the config model is absent, it will use `pydantic.BaseModel` by
        default, from which you cannot get any custom properties.
        :param name: the name of the addon.
        :param usage: the usage of the addon.
        :param description: the description of the addon.
        :param config_model: optional, the pydantic model of the addon's configurations.
        """

        self._name = name
        self._usage = usage
        self._config_model = config_model
        self._description = description
        self._rule_receiver: tuple[Rule, Callable[[], Awaitable[None]]] | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def usage(self) -> str:
        return self._usage

    @property
    def description(self) -> str:
        return self._description

    def receive(self, rule: Rule) -> Callable[[Callable[..., Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """
        Defines a receiver with itself injected. It detects whether your function is async
        automatically, so you can use both async and sync receivers.
        :param rule: the rule of the receiver.
        :return: injected receiver.
        """

        if self._rule_receiver:
            logger.warning(f'Duplicate rule and receiver for addon {self._name}, the old one will be overwritten.')

        def wrapper(handler: Any) -> Any:
            handler = di.inject(handler, sync=not asyncio.iscoroutinefunction(handler))  # type: ignore
            self._rule_receiver = rule, handler
            return handler

        return wrapper

    async def do_match(self) -> bool:
        """
        Applies the matcher to match whether this addon is matched.
        It will log a warning message if the matcher is absent.
        :return: whether it is matched.
        """

        if not self._rule_receiver:
            logger.warning(f'Attempted to match addon {self._name} when the rule is absent.')
            return False

        rule, _ = self._rule_receiver
        return await rule.match()

    async def do_receive(self) -> None:
        """
        Applies the receiver to receive events.
        It will log a warning message if the receiver is absent.
        """

        if not self._rule_receiver:
            logger.warning(f'Attempted to receive for addon {self._name} when the receiver is absent.')
            return

        def _provide_config(global_config: GlobalConfig) -> Any:
            return self._config_model.parse_obj(global_config.addons.get(self._name, {}))

        di.provide('config', _provide_config, sync=True, check_duplicate=False)

        _, receiver = self._rule_receiver
        await receiver()
