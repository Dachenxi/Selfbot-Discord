import discord
import asyncio
import modules
import logging
from discord.ext import commands


class VirtualFarmer(commands.Cog):
    def __init__(self, bot: modules.Bot):
        self.bot = bot


async def setup(bot: modules.Bot):
    await bot.add_cog(VirtualFarmer(bot))
