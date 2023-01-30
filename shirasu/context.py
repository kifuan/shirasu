from typing import Any, TYPE_CHECKING
from .message import Message, Text
from .logger import logger

if TYPE_CHECKING:
    from .client import Client


class Context:
    def __init__(self, client: "Client", data: dict[str, Any]) -> None:
        self._client = client
        self._data = data

    @property
    def user_id(self) -> int | None:
        return self._data.get('user_id')

    @property
    def group_id(self) -> int | None:
        return self._data.get('group_id')

    @property
    def notice(self) -> str:
        return self._data.get('notice', '')

    @property
    def message(self) -> str:
        return self._data.get('message', '')

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

    async def send(self, message: Message | str) -> int:
        if isinstance(message, str):
            message = Text(message)

        if group_id := self.group_id:
            return await self.send_group_msg(group_id, message)
        elif user_id := self.user_id:
            return await self.send_private_msg(user_id, message)

        logger.warning('Attempted to send message without group id or user id in the context.')
        return -1
