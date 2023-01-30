from pydantic import BaseModel
from shirasu import Context, Addon, command


class EchoConfig(BaseModel):
    add_echo_start: bool = False


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Echo what you send.',
    config_model=EchoConfig,
)


@echo.receive(command('echo'))
async def receive_echo(ctx: Context, config: EchoConfig) -> None:
    arg = ctx.arg
    if config.add_echo_start:
        arg = 'echo ' + arg
    await ctx.send(arg)
