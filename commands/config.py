import logging
from modules import Settings
from discord import Message
from discord.ext import commands

logger = logging.getLogger(__name__)

class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_object = Settings()

    @commands.command(name="showsettings")
    async def show_settings(self, ctx: Message):
        settings = self.settings_object.settings
        await ctx.channel.send(f"Current settings: {settings}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
    logger.info("Config command berhasil di load")