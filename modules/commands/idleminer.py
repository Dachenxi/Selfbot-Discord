import random

import discord
import asyncio
import modules
import logging
import re
import time
from discord.ext import commands, tasks


logger = logging.getLogger("idle miner")


async def _get_delay(message: discord.Message) -> int:
    if message:
        for embed in message.embeds:
            if embed.description:
                unix_time = re.search(r'<t:(\d+):R>', embed.description)
                time_now = int(time.time())
                if unix_time:
                    target_time = int(unix_time.group(1))
                    delay = target_time - time_now
                    if delay < 2:
                        delay = 5
                    elif delay > 600:
                        delay = 600
                    return delay
                break
    return 5

class IdleMiner(commands.Cog):
    def __init__(self, bot: modules.Bot):
        self.bot = bot
        self.message_id: int = 0
        self.channel: discord.TextChannel | None = None

    @tasks.loop(seconds=2)
    async def miner_tasks(self):
        try:
            message = await self.channel.fetch_message(self.message_id)
            if message:
                for row in message.components:
                    for children in row.children:
                        if (
                                isinstance(children, discord.Button) and
                                not children.disabled and
                                not (
                                        "playBoosters" in children.custom_id or
                                        "playPets" in children.custom_id or
                                        "playFarm" in children.custom_id
                                )
                        ):
                                    if "sell" in children.custom_id:
                                        for loop in range(5):
                                            await children.click()
                                            await asyncio.sleep(random.randint(3, 6))
                                    else:
                                        await children.click()
                delay = await _get_delay(message)
                await asyncio.sleep(delay)
            else:
                self.miner_tasks.cancel()
                logger.info("No buttons found, stopping miner task.")

        except Exception as e:
            if "COMPONENT_VALIDATION_FAILED" in str(e):
                pass
            elif "not receive" in str(e):
                pass
            else:
                logger.error(f"Error in miner task: {e}")

    @commands.command(name="cek_component", aliases=["cc"])
    async def cek_component(self, ctx: commands.Context):
        message_to_check = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        for component in message_to_check.components:
            for children in component.children:
                if isinstance(children, discord.Button):
                    print(children)

    @commands.command(name="miner", aliases=["m"])
    async def miner(self, ctx: commands.Context):
        self.channel = ctx.channel
        slash_command = await ctx.channel.application_commands()
        play_command = None
        for command in slash_command:
            if command.id == 1018127992590962708:
                play_command = command
                break
        if not play_command:
            await ctx.send("Could not find the play command.")
            return
        interaction = await play_command.__call__(ctx.channel)
        self.message_id = interaction.message.id
        if self.miner_tasks.is_running():
            self.miner_tasks.stop()
            await ctx.channel.send("Miner tasks stopped.")
        else:
            await self.miner_tasks.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild:
            match = re.search(r"<@(/d+)>", message.content)
            if "verification" in message.content and match and match.group(1) == self.bot.user.id and message.author.id == 518759221098053634:
                self.miner_tasks.stop()
        else:
            if message.author.id == 518759221098053634:
                self.miner_tasks.stop()
                await message.forward(self.bot.owner.dm_channel)
                await self.bot.owner.send(f"Please respond with {self.bot.command_prefix}verifidleminer <code>")
            elif message.author.id == self.bot.owner.id and message.content.startswith(self.bot.command_prefix):
                parts = message.content[1:].split()
                command_name = parts[0]
                if command_name == "verifidleminer":
                    code = parts[1] if len(parts) > 1 else ""
                    await message.reply("Verification command sent. idle miner task will resume.")
                    bot = self.bot.get_user(518759221098053634)
                    await bot.send(code)
                    if self.miner_tasks.is_running():
                        self.miner_tasks.stop()
                    await self.miner_tasks.start()


async def setup(bot: modules.Bot):
    await bot.add_cog(IdleMiner(bot))
    logger.info("IdleMiner cog has been set up.")