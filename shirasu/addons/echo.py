from ..addon import Addon, command
from ..context import Context


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Echo what you send.',
)


@echo.receive(command('echo'))
async def receive_echo(ctx: Context) -> None:
    await ctx.send(ctx.arg)
