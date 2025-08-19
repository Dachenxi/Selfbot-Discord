from modules import bot

async def setup_cogs():
    await bot.load_extension("modules.commands.utilities")