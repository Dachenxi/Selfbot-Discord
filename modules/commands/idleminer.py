from typing import assert_never

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

    @tasks.loop(seconds=2)
    async def miner_tasks(self, channel: discord.TextChannel):
        try:
            message = await channel.fetch_message(self.message_id)
            if message:
                for row in message.components:
                    for children in row.children:
                        if isinstance(children, discord.Button):
                            if not children.disabled:
                                if not ("Boosters" in children.custom_id or "Farm" in children.custom_id or "Pets" in children.custom_id):
                                    await children.click()

                delay = await _get_delay(message)
                print(delay)
                await asyncio.sleep(delay)
            else:
                self.miner_tasks.cancel()
                logger.info("No buttons found, stopping miner task.")
        except Exception as e:
            if "COMPONENT_VALIDATION_FAILED" in str(e):
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
        slash_command = await ctx.channel.application_commands()
        for command in slash_command:
            if command.id == 1018127992590962708:
                play_command = command
                break
        if not play_command:
            await ctx.send("Could not find the play command.")
            return
        interaction = await play_command.__call__(ctx.channel)
        self.message_id = interaction.message.id
        await self.miner_tasks.start(ctx.channel)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id:
            if "verification" in message.content and message.author.id == 518759221098053634:
                self.miner_tasks.stop()
        else:
            if message.author.id == 518759221098053634:
                self.miner_tasks.stop()
                await message.forward(self.bot.owner.dm_channel)

async def setup(bot: modules.Bot):
    await bot.add_cog(IdleMiner(bot))
    logger.info("IdleMiner cog has been set up.")