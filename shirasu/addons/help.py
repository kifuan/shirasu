from pydantic import BaseModel
from shirasu import Client, Addon, AddonPool, MessageEvent, command


class HelpConfig(BaseModel):
    show_addon_list: bool = True


help_addon = Addon(
    name='help',
    usage='/help addon_name',
    description='Prints usage description for certain addon.',
    config_model=HelpConfig,
)


FORMAT = '''
Name: {name}
Usage: {usage}
Description: {description}
'''.strip()


@help_addon.receive(command('help'))
async def handle_help(client: Client, config: HelpConfig, pool: AddonPool, event: MessageEvent) -> None:
    name = event.arg
    if not name:
        if not config.show_addon_list:
            await client.send('The configuration to show the addon list is turned off.')
            return
        else:
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
