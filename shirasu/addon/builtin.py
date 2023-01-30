from .addon import Addon
from .rule import regex
from ..context import Context


hello = Addon(
    name='hello',
    usage='hello',
    description='Sends world when received hello.',
)


@hello.receive(regex('^hello'))
async def receive_hello(ctx: Context):
    await ctx.send('world')
