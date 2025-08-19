from modules import bot

async def setup_cogs():
    await bot.load_extension("modules.commands.utilities")
    await bot.load_extension("modules.commands.virtualfisher")