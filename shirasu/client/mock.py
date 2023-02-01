import asyncio
from typing import Literal
from asyncio.queues import Queue

from .client import Client
from ..addon import AddonPool
from ..config import GlobalConfig
from ..event import Event, MessageEvent, mock_message_event
from ..message import Message


class MockClient(Client):
    def __init__(self, pool: AddonPool, global_config: GlobalConfig | None = None):
        super().__init__(pool, global_config or GlobalConfig())
        self._message_event_queue: Queue[MessageEvent] = Queue()

    async def post_event(self, event: Event) -> None:
        self.curr_event = event
        await self.apply_addons()

    async def send_msg(
            self,
            *,
            message_type: Literal['private', 'group'],
            user_id: int,
            group_id: int | None,
            message: Message,
            is_rejected: bool,
    ) -> int:
        await self._message_event_queue.put(mock_message_event(
            message_type=message_type,
            message=message,
            group_id=group_id,
            user_id=user_id,
            is_rejected=is_rejected,
        ))
        return -1

    async def get_message_event(self, timeout: float = .1) -> MessageEvent:
        return await asyncio.wait_for(self._message_event_queue.get(), timeout)

    async def get_message(self, timeout: float = .1) -> Message:
        return (await self.get_message_event(timeout)).message
