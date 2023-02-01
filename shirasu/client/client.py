import asyncio

from itertools import compress
from typing import Any, Literal
from abc import ABC, abstractmethod

from ..di import di
from ..addon import AddonPool
from ..config import GlobalConfig
from ..logger import logger
from ..event import Event, MessageEvent
from ..message import Message, MessageSegment, text


class ClientActionError(Exception):
    def __init__(self, data: dict[str, Any]):
        self.msg: str = data.get('msg', '')
        self.wording: str = data.get('wording', '')
        super().__init__(self.msg)


class Client(ABC):
    """
    The client to send and receive messages.
    """

    def __init__(self, pool: AddonPool, global_config: GlobalConfig):
        self.curr_event: Event | None = None
        self._pool = pool
        self._global_config = global_config
        di.provide('client', lambda: self, sync=True, check_duplicate=False)
        di.provide('pool', lambda: self._pool, sync=True, check_duplicate=False)
        di.provide('event', lambda: self.curr_event, sync=True, check_duplicate=False)
        di.provide('global_config', lambda: self._global_config, sync=True, check_duplicate=False)

    @abstractmethod
    async def send_msg(
            self,
            *,
            message_type: Literal['private', 'group'],
            user_id: int,
            group_id: int | None,
            message: Message,
            is_rejected: bool,
    ) -> int:
        raise NotImplementedError()

    async def send(self, message: Message | str | MessageSegment, *, is_rejected: bool = False) -> int:
        if not isinstance(self.curr_event, MessageEvent):
            logger.warning('Attempted to send message back when current event is not message event.')
            return -1

        if isinstance(message, str):
            message = text(message)
        if isinstance(message, MessageSegment):
            message = Message(message)

        return await self.send_msg(
            message=message,
            user_id=self.curr_event.user_id,
            group_id=self.curr_event.group_id,
            message_type=self.curr_event.message_type,
            is_rejected=is_rejected,
        )

    async def reject(self, message: Message | MessageSegment | str) -> int:
        """
        Rejects with a message, it only works for `MockClient` when testing.
        :param message: the message.
        :return: the message id.
        """

        return await self.send(message, is_rejected=True)

    async def apply_addons(self) -> None:
        """
        Applies all addons.
        """

        selectors = await asyncio.gather(*(addon.do_match() for addon in self._pool))
        matched_addons = list(compress(self._pool, selectors))

        if not (count := len(matched_addons)):
            return

        addon = matched_addons[0]
        if count > 1:
            logger.warning(f'Matched {count} conflict addons, only applies the first: {addon.name}.')

        await addon.do_receive()
