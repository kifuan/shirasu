from typing import Any, Literal
from datetime import datetime
from .message import Message, MessageSegment, text, parse_cq_message


class Event:
    def __init__(self, **params: Any) -> None:
        self.data = params
        self.time: int = params['time']
        self.self_id: int = params['self_id']
        self.post_type: str = params['post_type']

    def get(self, key: str) -> Any:
        return self.data.get(key)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> 'Event':
        return cls(**data)


class MessageEvent(Event):
    post_type: Literal['message']

    def __init__(self, **params: Any):
        super().__init__(**params)
        self.message_type: Literal['private', 'group'] = params['message_type']
        self.message: Message = params['parsed_message']
        self.user_id: int = params['user_id']
        self.group_id: int | None = params.get('group_id')
        self.is_rejected: bool = bool(params.get('is_rejected'))
        self.arg = ''

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> 'MessageEvent':
        return cls(
            parsed_message=parse_cq_message(data['raw_message']),
            **data,
        )

    def match_command(self, cmd: str, command_prefixes: list[str]) -> bool:
        t = self.message.plain_text
        for start in command_prefixes:
            prefix = start + cmd
            if t.startswith(prefix):
                self.arg = t.removeprefix(prefix).strip()
                return True
        return False


class NoticeEvent(Event):
    post_type: Literal['notice']

    def __init__(self, **params: Any):
        super().__init__(**params)
        self.notice_type: str = params['notice_type']


class RequestEvent(Event):
    post_type: Literal['request']

    def __init__(self, **params: Any):
        super().__init__(**params)
        self.request_type: str = params['request_type']


MOCK_SELF_ID = 1883
MOCK_USER_ID = 1884
MOCK_GROUP_ID = 1885


def mock_event(post_type: str, **params: Any) -> Event:
    return Event(
        time=datetime.utcnow().timestamp(),
        self_id=MOCK_SELF_ID,
        post_type=post_type,
        **params,
    )


def mock_message_event(
        message_type: Literal['group', 'private'],
        message: Message | MessageSegment | str,
        **params: Any
) -> MessageEvent:
    if isinstance(message, str):
        message = text(message)
    if isinstance(message, MessageSegment):
        message = Message(message)

    params.setdefault('user_id', MOCK_USER_ID)
    params.setdefault('group_id', MOCK_GROUP_ID)

    return MessageEvent(
        parsed_message=message,
        message_type=message_type,
        **mock_event(post_type='message').data,
        **params,
    )


def mock_notice_event(notice_type: str, **params: Any) -> NoticeEvent:
    return NoticeEvent(
        notice_type=notice_type,
        **mock_event(post_type='notice').data,
        **params,
    )


def mock_request_event(request_type: str, **params: Any) -> RequestEvent:
    return RequestEvent(
        request_type=request_type,
        **mock_event(post_type='request').data,
        **params,
    )
