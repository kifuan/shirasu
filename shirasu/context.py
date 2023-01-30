from typing import Any
from .client import Client
from .message import Message
from .logger import logger


class Context:
    def __init__(self, client: "Client", data: dict[str, Any]) -> None:
        self._client = client
        self._data = data

    async def send_private_msg(self, user_id: int, message: Message) -> int:
        msg = await self._client.call_action(
            action='send_private_msg',
            user_id=user_id,
            message=message.to_json_obj(),
        )
        return msg['message_id']

    async def send_group_msg(self, group_id: int, message: Message) -> int:
        msg = await self._client.call_action(
            action='send_group_msg',
            group_id=group_id,
            message=message.to_json_obj(),
        )
        return msg['message_id']

    async def send(self, message: Message) -> int:
        if group_id := self._data.get('group_id'):
            return await self.send_group_msg(group_id, message)
        elif user_id := self._data.get('user_id'):
            return await self.send_private_msg(user_id, message)

        logger.warning('Attempted to send message without group id or user id in the context.')
        return -1
