import random
import discord
import asyncio
import modules
import logging
import re
import time
from discord.ext import commands, tasks
from modules import TaskInterruptMixin


logger = logging.getLogger("Idle Miner Cog")


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
                    elif delay > 180:
                        delay = 180
                    return delay
                break
    return 5

class IdleMiner(commands.Cog, TaskInterruptMixin):
    def __init__(self, bot: modules.Bot):
        super().__init__()
        self.bot = bot
        self.data: dict = {}
        self.message_id: int = 0
        self.idle_miner_id = 518759221098053634
        self.miner_channel: discord.TextChannel | None = None
        self.farmer_channel: discord.TextChannel | None = None
        self.slash_command: dict[str, discord.SlashCommand | None] = {
            "plant": None,
            "harvest": None,
            "farm": None,
            "play": None
        }

    @tasks.loop(seconds=2)
    async def miner_tasks(self):
        try:
            message = await self.miner_channel.fetch_message(self.message_id)
            if message:
                for row in message.components:
                    for children in row.children:
                        if (
                                isinstance(children, discord.Button) and
                                not children.disabled and
                                not (
                                        children.label == "Boosters" or
                                        "playPets" in children.custom_id or
                                        "playFarm" in children.custom_id
                                )
                        ):
                                    if "playSell" in children.custom_id:
                                        for loop in range(5):
                                            await children.click()
                                            await asyncio.sleep(random.randint(3, 5))
                                    elif "playRebirth" in children.custom_id:
                                        await children.click()
                                        self.bot.telegram_notif.send_message(
                                            f"🔔Notification From Bot: {self.bot.user.name}\n"
                                            f"⌛Miner Tasks Perform Rebirth",
                                            83)
                                    elif "playPrestige" in children.custom_id:
                                        await children.click()
                                        self.bot.telegram_notif.send_message(
                                            f"🔔Notification From Bot: {self.bot.user.name}\n"
                                            f"⌛Miner Tasks Perform Prestige",
                                            83)
                                    else:
                                        await children.click()
                        if await self.interruptible_wait(random.randint(1, 2)):
                            return

                delay = await _get_delay(message)
                if await self.interruptible_wait(delay):
                    return
            else:
                self.interrupt(self.miner_tasks)
                await self.bot.embed.edit_embed(
                    self.bot.message_embed,
                    self.bot.tasks_update(
                        "Idle Miner",
                        "Farmer tasks",
                        "🔴 Not Running"))
                logger.info("No buttons found, stopping miner task.")

        except Exception as e:
            if "COMPONENT_VALIDATION_FAILED" in str(e):
                pass
            elif "not receive" in str(e):
                await asyncio.sleep(random.randint(60, 120))
            else:
                logger.error(f"Error in miner task: {e}")
                pass

    @tasks.loop(seconds=1)
    async def idle_miner_farm_tasks(self, crops: str = "carrot"):
        await self.slash_command["harvest"].__call__(self.farmer_channel, area="all")
        await asyncio.sleep(1)
        await self.slash_command["plant"].__call__(self.farmer_channel, area="all", crop=crops)
        await asyncio.sleep(1)

        farm_interaction = await self.slash_command["farm"].__call__(self.farmer_channel)
        farm_message = await self.farmer_channel.fetch_message(farm_interaction.message.id)
        hours = 0
        minute = 0
        second = 0
        total_xp = 0
        next_level_xp = 0

        for embed in farm_message.embeds:
            minute, second = re.search(r"crop ready in (\d+)m(\d+)s", embed.description).groups()
            for field in embed.fields:
                if "level" in field.name.lower():
                    total_xp, next_level_xp = re.search(r"Total xp: ([\d,]+)\nNext level at: ([\d,]+)xp", field.value).groups()

        self.bot.telegram_notif.send_message(
            f"🔔Notification From Bot: {self.bot.user.name}\n"
            f"🪵Plant Corps: {crops}\n"
            f"⌛Next Harvest in {minute}m{second}s\n"
            f"⭐Current XP: {total_xp} XP\n"
            f"🌟Next Level at: {next_level_xp} XP",
            80
        )
        if await self.interruptible_wait((int(minute) * 60) + int(second)):
            return

    @commands.command(name="miner", aliases=["m"])
    async def miner(self, ctx: commands.Context):
        self.clear_interrupt()

        if self.miner_tasks.is_running():
            self.interrupt(self.miner_tasks)

            await self.bot.embed.edit_embed(
                self.bot.message_embed,
                self.bot.tasks_update(
                    "Idle Miner",
                    "Miner tasks",
                    "🔴 Not Running"))

            await ctx.channel.send("Miner tasks stopped.")
        else:
            interaction = await self.slash_command["play"].__call__(self.miner_channel)
            self.message_id = interaction.message.id

            await self.bot.embed.edit_embed(
                self.bot.message_embed,
                self.bot.tasks_update(
                    "Idle Miner",
                    "Miner tasks",
                    "🟢 Running"))

            await self.miner_tasks.start()

    @commands.command(name="idleminerfarmer", aliases=["imf"])
    async def idleminerfarmer(self, ctx: commands.Context, crops:str = "carrot"):
        self.clear_interrupt()

        if self.idle_miner_farm_tasks.is_running():
            self.interrupt(self.idle_miner_farm_tasks)

            await self.bot.embed.edit_embed(
                self.bot.message_embed,
                self.bot.tasks_update(
                    "Idle Miner",
                    "Farmer tasks",
                    "🔴 Not Running"))

            await ctx.channel.send("Idle miner farmer tasks stopped.")
        else:

            await self.bot.embed.edit_embed(
                self.bot.message_embed,
                self.bot.tasks_update(
                    "Idle Miner",
                    "Farmer tasks",
                    "🟢 Running"))

            await self.idle_miner_farm_tasks.start(crops=crops)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            if (
                    message.author.id == self.idle_miner_id
                    and "code" in message.content.lower()
            ):
                self.interrupt(self.miner_tasks)

                await self.bot.embed.edit_embed(
                    self.bot.message_embed,
                    self.bot.tasks_update(
                        "Idle Miner",
                        "Farmer tasks",
                        "🔴 Not Running"))

                self.bot.telegram_notif.send_message(f"🔔Notification From Bot: {self.bot.user.name}\n"
                                                     f"🤖Anti Bot Message from idle miner is detected\n"
                                                     f"✉️Message Content: {message.content}\n"
                                                     f"🔗Link to image captcha: {message.attachments[0].url if message.attachments else 'No attachment found.'}",
                                                     message_thread_id=69)
                await message.forward(self.bot.owner.dm_channel)
                await self.bot.owner.send(f"Please respond with {self.bot.command_prefix}verifim <code>")

            elif (
                    message.author.id == self.bot.owner.id
                    and message.content.startswith(self.bot.command_prefix)
            ):
                parts = message.content[1:].split()
                command_name = parts[0]
                if command_name == "verifim":
                    code = parts[1] if len(parts) > 1 else ""
                    await message.reply("Verification command sent. idle miner task will resume.")
                    idle_miner_bot = self.bot.get_user(self.idle_miner_id)
                    await idle_miner_bot.send(code)
                else:
                    return
            elif (
                    message.author.id == self.idle_miner_id
                    and "continue" in message.content.lower()
            ):
                self.clear_interrupt()
                if self.miner_tasks.is_running():
                    self.interrupt(self.miner_tasks)
                await self.miner_tasks.start()

    async def idle_miner_setup(self):
        logger.info("Setting up Idle Miner")
        data_database = await self.bot.database.fetch("SELECT * FROM idle_miner WHERE user_id = %s",
                                                      (self.bot.user.id,),
                                                      True)
        if not data_database:
            logger.warning("Idle miner data not found in database, creating a new entry.")
            miner_channel_id = int(input("Enter miner channel ID for Idle Miner: "))
            farmer_channel_id = int(input("Enter farmer channel ID for Idle Miner Farmer: "))
            await self.bot.database.execute("INSERT INTO idle_miner (user_id, farmer_channel_id, miner_channel_id) VALUES (%s, %s, %s)",
                                            (self.bot.user.id, farmer_channel_id, miner_channel_id))
            logger.info("Idle miner data has been created in the database.")
            data_database = await self.bot.database.fetch("SELECT * FROM idle_miner WHERE user_id = %s",
                                                          (self.bot.user.id,),
                                                          True)
        self.data = data_database
        await asyncio.sleep(1)
        self.miner_channel = self.bot.get_channel(self.data['miner_channel_id'])
        self.farmer_channel = self.bot.get_channel(self.data['farmer_channel_id'])
        if not self.miner_channel:
            logger.error("Channel not found. Please update the channel ID.")
            return

        logger.info(f"Get Idle Miner Slash Command for Idle Miner in channel {self.miner_channel.name} or {self.farmer_channel.name}")
        await asyncio.sleep(1)
        slash_command = await self.miner_channel.application_commands()
        for command in slash_command:
            if command.id == 968186271971287110:
                self.slash_command["plant"] = command
            elif command.id == 968186273284096030:
                self.slash_command["harvest"] = command
            elif command.id == 968186270197121044:
                self.slash_command["farm"] = command
            elif command.id == 1018127992590962708:
                self.slash_command["play"] = command
            if all(self.slash_command.values()):
                break
        if not all(self.slash_command.values()):
            logger.error("Some of the Idle Miner Slash Command is not found, Check Again.")
            return

        logger.info("Idle Miner Slash Command Is Ready to use.")

async def setup(bot: modules.Bot):
    await bot.add_cog(IdleMiner(bot))
    logger.info("IdleMiner cog has been set up.")