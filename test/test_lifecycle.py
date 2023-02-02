import asyncio

import pytest
from shirasu import AddonPool, Addon, MockClient, lifecycle, Client, Message, text
from shirasu.event import MOCK_USER_ID, mock_meta_event


MESSAGE_TEXT = 'hello'


send_on_connected = Addon(
    name='send_on_connected',
    usage='',
    description=''
)


@send_on_connected.receive(lifecycle('connected'))
async def handle_connected(client: Client) -> None:
    await client.send_msg(
        message_type='private',
        user_id=MOCK_USER_ID,
        group_id=None,
        message=Message(text(MESSAGE_TEXT)),
        is_rejected=False,
    )


@pytest.mark.asyncio
async def test_lifecycle_connected():
    pool = AddonPool().load(send_on_connected)
    client = MockClient(pool)

    await client.post_event(mock_meta_event(
        meta_event_type='lifecycle',
        sub_type='connected',
    ))
    msg = await client.get_message()
    assert msg.plain_text == MESSAGE_TEXT

    # Should not reply to heartbeat meta events.
    await client.post_event(mock_meta_event(
        meta_event_type='heartbeat',
    ))
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()

