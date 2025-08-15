import discord
import logging
from modules import Bot
from discord.ext import commands

logger = logging.getLogger(__name__)

class Setup(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="setup")
    async def setup(self, ctx: discord.Message):
        """
        Set up to retrieve owner ID and guild ID
        :param ctx:
        """
        if not ctx.guild:
            await ctx.reply("This command can only be used in a server.")
            return
        self.bot.setting.set("main_server", ctx.guild.id)
        self.bot.setting.set("owner_id", ctx.guild.owner_id)
        await ctx.channel.send(f"Owner ID set to {ctx.author.id} and Guild ID set to {ctx.guild.id}.")

async def setup(bot: commands.Bot):
    """
    Load the setup cog.
    This is used to set up the bot with the owner ID and guild ID.
    """
    await bot.add_cog(Setup(bot))
    logger.info("Setup commands loaded successfully.")