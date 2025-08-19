import logging
import random
import modules
import asyncio
from discord.ext import commands, tasks
from discord import TextChannel, SlashCommand

logger = logging.getLogger(__name__)

# noinspection PyTypeChecker
class VirtualFisher(commands.Cog):
    def __init__(self, bot: modules.Bot) -> None:
        self.data: dict = None
        self.bot = bot
        self.channel: TextChannel = None
        self.sell_command: SlashCommand = None
        self.fish_command: SlashCommand = None
        self.verify_command: SlashCommand = None

    @tasks.loop(seconds=5)
    async def fisher_tasks(self):
        if self.channel is None:
            logger.warning("Channel is not set, skipping fisher task")
            return

        self.data["trips"] += 1
        await self.fish_command.__call__(self.channel)
        await asyncio.sleep(random.randint(60, 600))

    async def _load_slash_commands(self, channel: TextChannel):
        slash_commands = await channel.application_commands()
        if not (
                self.sell_command
                or self.fish_command
                or self.verify_command
        ):
            for cmd in slash_commands:
                if cmd.id == 912432960643416115:
                    self.fish_command = cmd
                elif cmd.id == 912432960643416116:
                    self.sell_command = cmd
                elif cmd.id == 912432961222238220:
                    self.verify_command = cmd
                if self.fish_command and self.sell_command and self.verify_command:
                    break

    @commands.command(name="fisher")
    async def fisher(self, ctx: commands.Context):
        self.channel = ctx.channel
        if self.fisher_tasks.is_running():
            await ctx.channel.send("Fisher task is already running.")
            return

        await self._load_slash_commands(ctx.channel)
        if not (self.fish_command or self.sell_command):
            await ctx.channel.send("Failed to find slash command object")
            return

        await self.fisher_tasks.start()
        await ctx.channel.send("Fisher is starting")

    @commands.command(name="stopfisher")
    async def stopfisher(self, ctx: commands.Context):
        if not self.fisher_tasks.is_running():
            await ctx.channel.send("Fisher task is not running.")
            return

        self.fisher_tasks.stop()
        await ctx.channel.send("Fisher task has been stopped.")

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Setting up VirtualFisher Database")
        data = await self.bot.database.fetch("SELECT * FROM virtualfisher WHERE user_id = %s",
                                             (self.bot.user.id,),
                                             one=True)
        # If no data, create a new entry
        if not data:
            logger.warning("Data not found, Creating VirtualFisher Database")
            await self.bot.database.execute("INSERT INTO virtualfisher (user_id) VALUES (%s)",
                                            (self.bot.user.id,))
            data = await self.bot.database.fetch("SELECT * FROM virtualfisher WHERE user_id = %s",
                                                 (self.bot.user.id,),
                                                 one=True)
            self.data = data
        else:
            self.data = data

async def setup(bot: commands.Bot):
    await bot.add_cog(VirtualFisher(bot))
    logger.info("VirtualFisher command successfully loaded")