import pytest
from shirasu import MockClient, mock_message_event

GROUP_ID = 1883
SELF_ID = 1


@pytest.mark.asyncio
async def test_echo():
    client = MockClient()
    client.pool.load_module('shirasu.addons.echo')
    await client.post_event(mock_message_event('group', '/echo hello'))
    msg = await client.get_message()
    assert msg.message.plain_text == 'hello'
