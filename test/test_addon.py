import pytest
import asyncio
from shirasu import MockClient, AddonPool
from shirasu.event import mock_message_event
from shirasu.addon import (
    DuplicateAddonError,
    LoadAddonError,
)


def test_pool_load_error():
    pool = AddonPool()
    pool.load_module('shirasu.addons.echo')

    with pytest.raises(DuplicateAddonError):
        pool.load_module('shirasu.addons.echo')

    with pytest.raises(LoadAddonError):
        pool.load_module('@dummy_module')


@pytest.mark.asyncio
async def test_echo():
    pool = AddonPool.from_modules('shirasu.addons.echo')
    client = MockClient(pool)

    await client.post_event(mock_message_event('group', '/echo hello'))

    msg = await client.get_message()
    assert msg.plain_text == 'hello'

    await client.post_event(mock_message_event('group', 'echo hello'))
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()


@pytest.mark.asyncio
async def test_square():
    pool = AddonPool.from_modules('shirasu.addons.square')
    client = MockClient(pool)

    await client.post_event(mock_message_event('group', '/square 2'))
    square2_msg = await client.get_message()
    assert square2_msg.plain_text == '4'

    await client.post_event(mock_message_event('group', '/square a'))
    rejected_msg = await client.get_message_event()
    assert rejected_msg.is_rejected
