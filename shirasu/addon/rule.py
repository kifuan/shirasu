import re
import asyncio
import operator
from typing import cast, Union, Callable, Awaitable

from ..di import di
from ..event import Event, MessageEvent, NoticeEvent
from ..config import GlobalConfig


class Rule:
    """
    The rule to match whether the message should be applied to current addon.
    Note: the handler will be injected automatically.
    """

    def __init__(self, handler: Callable[..., Awaitable[bool]]):
        self._handler = di.inject(handler)

    def __or__(self, rule: 'Rule') -> 'Rule':
        return self._compose(rule, operator.or_)

    def __and__(self, rule: 'Rule') -> 'Rule':
        return self._compose(rule, operator.and_)

    def _compose(self, rule: 'Rule', op: Callable[[bool, bool], bool]) -> 'Rule':
        async def handler() -> bool:
            res = await asyncio.gather(self.match(), rule.match())
            return op(*res)
        return Rule(handler)

    async def match(self) -> bool:
        """
        Runs the matcher of this rule.
        :return: whether or not matched.
        """

        return await self._handler()


def message() -> Rule:
    """
    The rule to match message events.
    :return: the rule.
    """

    async def handler(event: Event) -> bool:
        return event.post_type == 'message'
    return Rule(handler)


def command(cmd: str) -> Rule:
    """
    The rule to match certain command.
    :param cmd: the command.
    :return: the rule.
    """

    async def handler(event: MessageEvent, global_config: GlobalConfig) -> bool:
        return event.match_command(cmd, global_config.command_start)

    return message() & Rule(handler)


def regex(r: Union[str, re.Pattern]) -> Rule:
    """
    The rule to match certain regex.
    :param r: regex, whether or not compiled.
    :return: the rule.
    """

    if isinstance(r, str):
        r = re.compile(r)

    async def handler(event: MessageEvent) -> bool:
        return bool(r.match(event.message.plain_text))  # type: ignore

    return message() & Rule(handler)


def notice(notice_type: str) -> Rule:
    """
    The rule to match certain notice.
    :param notice_type: the notice type.
    :return the rule.
    """

    async def handler(event: Event) -> bool:
        if event.post_type != 'notice':
            return False
        return cast(NoticeEvent, event).notice_type == notice_type

    return Rule(handler)
