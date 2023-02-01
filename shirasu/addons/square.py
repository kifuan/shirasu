from shirasu import Client, Addon, MessageEvent, command


square = Addon(
    name='square',
    usage='/square number',
    description='Calculates the square of given number.',
)


@square.receive(command('square'))
async def receive_square(client: Client, event: MessageEvent) -> None:
    arg = event.arg

    try:
        await client.send(f'{pow(float(arg), 2):g}')
    except ValueError:
        await client.reject(f'Invalid number: {arg}')
