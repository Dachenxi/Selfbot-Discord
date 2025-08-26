import discord
import asyncio
import logging
import modules
from discord.ext import commands, tasks

logger = logging.getLogger("owo_modules")

class OWO(commands.Cog):
    def __init__(self, bot: modules.Bot):
        self.bot = bot
        self.channel = None

    @tasks.loop(seconds=20)
    async def hunt_tasks(self):
        try:
            await self.channel.send("owo hunt")
        except Exception as e:
            logger.error(e)
            await asyncio.sleep(20)

    @tasks.loop(seconds=20)
    async def battle_tasks(self):
        try:
            await self.channel.send("owo battle")
        except Exception as e:
            logger.error(e)
            await asyncio.sleep(20)


    @commands.command(name="hunt_owo", aliases=["ho"])
    async def hunt_owo(self, ctx: commands.Context):
        self.channel = ctx.channel
        if self.hunt_tasks.is_running():
            await ctx.channel.send("Hunt owo is already running.")
            self.hunt_tasks.stop()
            return
        else:
            await ctx.channel.send("Hunt owo starting...")
            self.hunt_tasks.start()

    @commands.command(name="battle_owo", aliases=["bo"])
    async def battle_owo(self, ctx: commands.Context):
        self.channel = ctx.channel
        if self.battle_tasks.is_running():
            await ctx.channel.send("Battle owo is already running.")
            self.battle_tasks.stop()
            return
        else:
            await ctx.channel.send("Battle owo starting...")
            self.battle_tasks.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            if message.author.id == 408785106942164992:
                self.hunt_tasks.stop()
                self.battle_tasks.stop()
                logger.info("Stopping hunt and battle tasks because DM received from OWO bot.")
                await message.forward(self.bot.owner.dm_channel)
                await self.bot.owner.send("Please reply with code `!owo <code>` to send the code to OWO bot.")
            elif message.author.id == self.bot.owner.id and message.content.startswith(self.bot.command_prefix):
                parts = message.content[1:].split()
                command_name = parts[0]
                if command_name == "owo":
                    code = parts[1]
                    bot = self.bot.get_user(408785106942164992)
                    await bot.send(f"{code}")



        else:
            if message.embeds and message.author.id == 408785106942164992 and message.guild.id == self.bot.guild_id:
                if self.bot.user.global_name in message.embeds[0].author.name:
                    self.bot.telegram_notif.send_message(f"Notification From User: {self.bot.user.global_name}\n\n"
                                                         f"Get Message By OWO Bot: \n{message.embeds[0].footer.text}",
                                                         message_thread_id=19)



async def setup(bot):
    await bot.add_cog(OWO(bot))
    logger.info("OWO module loaded")