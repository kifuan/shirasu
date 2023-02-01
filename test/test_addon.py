import pytest
import asyncio
from shirasu import MockClient, AddonPool
from shirasu.event import mock_message_event
from shirasu.addon import (
    DuplicateAddonError,
    NoSuchAddonError,
    LoadAddonError,
)


@pytest.mark.asyncio
async def test_echo():
    pool = AddonPool.from_modules('shirasu.addons.echo')
    client = MockClient(pool)

    await client.post_event(mock_message_event('group', '/echo hello'))

    msg = await client.get_message()
    assert msg.message.plain_text == 'hello'

    await client.post_event(mock_message_event('group', 'echo hello'))
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()


def test_duplicate_addon():
    pool = AddonPool()
    pool.load_module('shirasu.addons.echo')

    with pytest.raises(DuplicateAddonError):
        pool.load_module('shirasu.addons.echo')


def test_no_such_addon():
    pool = AddonPool()

    with pytest.raises(NoSuchAddonError):
        pool.get_addon('dummy')


def test_load_error_addon():
    pool = AddonPool()

    with pytest.raises(LoadAddonError):
        pool.load_module('@dummy_module')
