from typing import Callable, Awaitable, Any

from ..di import di
from .rule import Rule
from ..logger import logger


class Addon:
    """
    The addon to define addons, providing decorator `receive` to define receivers.
    Note: functions decorated by `receive` will also be injected.
    """

    def __init__(self, *, name: str, usage: str, description: str) -> None:
        self._name = name
        self._usage = usage
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
        Defines a receiver handler with itself injected.
        :param rule: the rule of the receiver.
        :return: injected receiver handler.
        """

        if self._rule_receiver:
            logger.warning(f'Duplicate rule and receiver for addon {self._name}, the old one will be overwritten.')

        def wrapper(handler: Any) -> Any:
            handler = di.inject(handler)
            self._rule_receiver = rule, handler
            return handler

        return wrapper

    async def do_receive(self) -> None:
        if not self._rule_receiver:
            logger.warning(f'Attempted to receive for addon {self._name} when receiver and rule is absent.')
            return

        rule, receiver = self._rule_receiver
        if not await rule.match():
            return

        logger.info(f'Matched addon {self._name}.')
        await receiver()

