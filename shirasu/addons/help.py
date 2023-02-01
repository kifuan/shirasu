from shirasu import Client, Addon, AddonPool, MessageEvent, command


help_addon = Addon(
    name='help',
    usage='/help addon_name',
    description='Prints usage description for certain addon.',
)


FORMAT = '''
Name: {name}
Usage: {usage}
Description: {description}
'''.strip()


@help_addon.receive(command('help'))
async def receive_echo(client: Client, pool: AddonPool, event: MessageEvent) -> None:
    name = event.arg
    if not name:
        addons = ', '.join(a.name for a in pool)
        await client.send(f'Available addons: {addons}')
        return

    if addon := pool.get_addon(name):
        await client.send(FORMAT.format(
            name=addon.name,
            usage=addon.usage,
            description=addon.description,
        ))
        return

    await client.send(f'Addon {name} is not found.')
