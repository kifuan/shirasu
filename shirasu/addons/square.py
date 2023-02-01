from pydantic import BaseModel
from shirasu import Client, Addon, MessageEvent, command


class SquareConfig(BaseModel):
    precision: int = 2


square = Addon(
    name='square',
    usage='/square number',
    description='Calculates the square of given number.',
    config_model=SquareConfig,
)


@square.receive(command('square'))
async def handle_square(client: Client, event: MessageEvent, config: SquareConfig) -> None:
    arg = event.arg

    try:
        result = round(float(arg) ** 2, config.precision)
        await client.send(f'{result:g}')
    except ValueError:
        await client.reject(f'Invalid number: {arg}')
