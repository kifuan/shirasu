import pytest
import asyncio
from shirasu import MockClient, AddonPool, mock_message_event


@pytest.mark.asyncio
async def test_echo():
    pool = AddonPool()
    pool.load_module('shirasu.addons.echo')
    client = MockClient(pool=pool)

    await client.post_event(mock_message_event('group', '/echo hello'))

    msg = await client.get_message()
    assert msg.message.plain_text == 'hello'

    await client.post_event(mock_message_event('group', 'echo hello'))
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()
