from shirasu import Context, Addon, command


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Echo what you send.',
)


@echo.receive(command('echo'))
async def receive_echo(ctx: Context) -> None:
    await ctx.send(ctx.arg)
