import datetime
import logging
import random
import modules
import asyncio
import re
import json
import discord
from discord.ext import commands, tasks
from discord import TextChannel, SlashCommand, Interaction, Message, Embed

logger = logging.getLogger(__name__)

# noinspection PyTypeChecker
class VirtualFisher(commands.Cog):
    def __init__(self, bot: modules.Bot) -> None:
        self.data: dict = None
        self.bot = bot
        self.channel: TextChannel = None
        self.sell_command: SlashCommand = None
        self.fish_command: SlashCommand = None
        self.buy_command: SlashCommand = None
        self.verify_command: SlashCommand = None

    @tasks.loop(seconds=5)
    async def fisher_tasks(self):
        try:
            if self.channel is None:
                logger.warning("Channel is not set, skipping fisher task")
                return

            self.data["trips"] += 1
            interaction = await self.fish_command.__call__(self.channel)
            await self._check_interaction(interaction)
            if self.data["trips"] % 10 == 0:
                interaction = await self.sell_command.__call__(self.channel, amount="all")
                await self._check_interaction(interaction)

            await self.bot.database.execute("UPDATE virtualfisher SET trips = %s WHERE user_id = %s",
                                            (self.data["trips"], self.bot.user.id))
            await asyncio.sleep(random.randint(300, 600))
        except discord.InvalidData:
            logger.error("Invalid data received, stopping fisher tasks.")
            await asyncio.sleep(random.randint(300, 600))

    @tasks.loop(seconds=5)
    async def worker_tasks(self):
        try:
            if self.data["emerald_fish"] >= 8:
                interaction = await self.buy_command.__call__(self.channel, item="Auto30m")
                self.data["emerald_fish"] -= 8
                await self.bot.database.execute("UPDATE virtualfisher SET emerald_fish = %s WHERE user_id = %s",
                                                (self.data["emerald_fish"], self.bot.user.id))
                delay = await self._check_interaction(interaction)
                await asyncio.sleep(delay)
            elif self.data["gold_fish"] >= 8:
                interaction = await self.buy_command.__call__(self.channel, item="Auto10m")
                self.data["gold_fish"] -= 8
                await self.bot.database.execute("UPDATE virtualfisher SET gold_fish = %s WHERE user_id = %s",
                                                (self.data["gold_fish"], self.bot.user.id))
                delay = await self._check_interaction(interaction)
                await asyncio.sleep(delay)
            else:
                logger.info("Not enough exotic fish to buy worker, stopping now")
                self.worker_tasks.stop()

        except discord.ConnectionClosed:
            logger.warning("It seems the connection was closed, restarting worker tasks in 5 to 10 minutes.")
            await asyncio.sleep(random.randint(300, 600))
        except discord.InvalidData:
            logger.error("Invalid data received, restarting in 5 to 10 minutes.")
            await asyncio.sleep(random.randint(300, 600))

    async def _check_interaction(self, interaction: Interaction):
        try:
            interaction_message = await self.channel.fetch_message(interaction.message.id)
            if interaction_message is None:
                logger.warning("Message not found")
                return None

            if not interaction_message.embeds:
                logger.warning("Embeds not found in interaction message")
                return None

            for embed in interaction_message.embeds:
                if (
                        embed.description is not None
                        and "your worker" in embed.description.lower()
                ):
                    await self._worker_check(embed)
                if (
                        embed.title is not None
                        and ("anti-bot" in embed.title.lower() or
                             "code" in embed.description.lower() or
                             "verify" in embed.description.lower())
                ):
                    logger.warning("Anti-Bot message detected")
                    await self._anti_bot_resolve(embed, interaction_message)
                if (
                    embed.description is not None
                    and "hired" in embed.description.lower()
                ):
                    logger.info("Hired worker message detected")
                    delay = await self._worker_hired(embed)
                    return delay
                if (
                    embed.description is not None
                    and ("emerald" in embed.description.lower() or
                         "gold" in embed.description.lower())
                ):
                    logger.info("Exotic fish message detected")
                    await self._exotic_fish(embed)

                if (
                    embed.description is not None
                    and ("$" in embed.description.lower() or
                         "sold" in embed.description.lower())
                ):
                    await self._money(embed)

        except Exception as e:
            logger.error(f"Error in check interaction: {e}")

    async def _money(self, embed: Embed):
        notif = {
            "title": "Money Notification",
            "username": self.bot.user.name,
            "balance": 0,
            "get_money": 0,
            "total_balance": self.data["balance"],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        money_search = re.search(r"\*\*?\$([\d,]+)\*\*?", embed.description)
        if money_search is not None:
            money = int(money_search.group(1).replace(",", ""))
            notif["balance"] = self.data["balance"]
            notif["get_money"] = money
            notif["total_balance"] += money
            self.data["balance"] = notif["total_balance"]

            await self.bot.database.execute("UPDATE virtualfisher SET balance = %s WHERE user_id = %s",
                                            (self.data["balance"], self.bot.user.id))
            self.bot.telegram_notif.send_message(f"```json\n{json.dumps(notif, indent=4)}\n```")
        else:
            logger.warning("Money embed is detected but no money found in description")

    async def _worker_hired(self, embed: Embed):
        search = re.search(r"the next \*\*(\d+)\*\* minutes", embed.description)
        if search is not None:
            delay = int(search.group(1))
            text = {
                "title": "Worker Hired",
                "username": self.bot.user.name,
                "description": f"Worker hired for the next {delay} minutes",
                "delay": delay * 60,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.bot.telegram_notif.send_message(f"```json\n{json.dumps(text, indent=4)}\n```")
            return delay * 60  # Convert minutes to seconds
        else:
            logger.warning("No delay found in worker hired message, using default")
            return 1900

    async def _worker_check(self, embed: Embed):
        total_fish = re.search(r"total of \*\*(\d+)\*\* fish", embed.description)
        if total_fish:
            notif = {
                "title": "Fish from Worker Notification",
                "username": self.bot.user.name,
                "total_fish": int(total_fish.group(1)),
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.bot.telegram_notif.send_message(f"```json\n{json.dumps(notif, indent=4)}\n```")
        else:
            logger.warning("Got nothing from worker fish")
            return

    async def _anti_bot_resolve(self, embed: Embed, message: Message):
        """Anti bot message example:
        Code: **D8fQ**\n\nPlease use **/verify ``D8fQ``** to continue playing."""
        notif_message = {
            "title": "Anti-Bot Message Detected",
            "username": self.bot.user.name,
            "code": "None",
            "embed": json.dumps(embed.to_dict(), indent=4),
            "isimage": {
                "status": "No",
                "message": "No image detected in embed"
            },
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        notif = self.bot.telegram_notif.send_message(f"```json\n{json.dumps(notif_message, indent=4)}\n```")
        code_search = re.search(r"Code: \*\*(\w+)\*\*", embed.description)
        if code_search:
            code = code_search.group(1)
            self.bot.telegram_notif.edit_message(int(notif["result"]["message_id"]),
                                                 f"```json\n{json.dumps(notif_message, indent=4)}\n```")
            await self.verify_command.__call__(self.channel, answer=code)
            await self.fisher_tasks.start()

        else:
            notif_message["isimage"]["status"] = "Yes"
            notif_message["isimage"]["message"] = "Image is detected, forward message to owner for manual solve"

            self.bot.telegram_notif.edit_message(int(notif["result"]["message_id"]),
                                                 f"```json\n{json.dumps(notif_message, indent=4)}\n```")
            self.fisher_tasks.stop()
            await message.forward(self.bot.owner)

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
                elif cmd.id == 912432961134166090:
                    self.buy_command = cmd
                if self.fish_command and self.sell_command and self.verify_command and self.buy_command:
                    break

    async def _exotic_fish(self, embed: Embed):
        emerald_fish = re.search(r"You got (\d+) Emerald Fish", embed.description)
        gold_fish = re.search(r"You got (\d+) Gold Fish", embed.description)

        if emerald_fish:
            self.data["emerald_fish"] += int(emerald_fish.group(1))
            await self.bot.database.execute("UPDATE virtualfisher SET emerald_fish = %s WHERE user_id = %s",
                                            (self.data["emerald_fish"], self.bot.user.id))
            notif = {"title": "You Found Crate",
                        "username": self.bot.user.name,
                     "containing":
                         {"emerald_fish": emerald_fish.group(1)},
                     "exotic_fish":
                         {"emerald_fish": self.data["emerald_fish"],
                          "gold_fish": self.data["gold_fish"]}
                     }
            self.bot.telegram_notif.send_message(f"```json\n{json.dumps(notif, indent=4)}\n```")

        if gold_fish:
            self.data["gold_fish"] += int(gold_fish.group(1))
            await self.bot.database.execute("UPDATE virtualfisher SET gold_fish = %s WHERE user_id = %s",
                                            (self.data["gold_fish"], self.bot.user.id))
            notif = {"title": "You Found Crate",
                     "username": self.bot.user.name,
                     "containing":
                         {"gold_fish": gold_fish.group(1)},
                     "exotic_fish":
                         {"emerald_fish": self.data["emerald_fish"],
                          "gold_fish": self.data["gold_fish"]}
                     }
            self.bot.telegram_notif.send_message(f"```json\n{json.dumps(notif, indent=4)}\n```")

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

    @commands.command(name="stopfisher", aliases=["sf"])
    async def stopfisher(self, ctx: commands.Context):
        if not self.fisher_tasks.is_running():
            await ctx.channel.send("Fisher task is not running.")
            return

        self.fisher_tasks.stop()
        await ctx.channel.send("Fisher task has been stopped.")

    @commands.command(name="worker")
    async def worker(self, ctx: commands.Context):
        self.channel = ctx.channel
        if self.worker_tasks.is_running():
            await ctx.channel.send("Worker task is already running.")
            return
        await self._load_slash_commands(ctx.channel)
        if not self.buy_command:
            await ctx.channel.send("Failed to find buy slash command object")
            return
        await self.worker_tasks.start()
        await ctx.channel.send("Worker task is starting")

    @commands.command(name="stopworker", aliases=["sw"])
    async def stopworker(self, ctx: commands.Context):
        if not self.worker_tasks.is_running():
            await ctx.channel.send("Worker task is not running.")
            return

        self.worker_tasks.stop()
        await ctx.channel.send("Worker task has been stopped.")

    @commands.command(name="getvf", aliases=["gvf"])
    async def getvf(self, ctx: commands.Context):
        reply_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if not reply_message:
            await ctx.channel.send("Please reply to virtual fish inventory")
            return

        # Regex pattern
        money_pattern = r"Balance: \*\*?\$([\d,]+)\*\*?"
        clan_patten = r"Clan: \*\*(\w+)\*\*"
        biome_pattern = r"Current biome: <:\w+:\d+> \*\*(\w+)\*\*"
        gold_fish_pattern = r"\*\*([\d,]+)\*\* <:\w+:\d+> Gold Fish"
        emerald_fish_pattern = r"\*\*([\d,]+)\*\* <:\w+:\d+> Emerald Fish"

        if not "inventory" in reply_message.embeds[0].title.lower():
            await ctx.channel.send("Please reply to a valid virtual fish inventory message. That only has inventory embed in it")
            return

        # Extracting data using regex
        money_match = re.search(money_pattern, reply_message.embeds[0].description)
        clan_match = re.search(clan_patten, reply_message.embeds[0].description)
        biome_match = re.search(biome_pattern, reply_message.embeds[0].description)
        gold_fish_match = re.search(gold_fish_pattern, reply_message.embeds[0].description)
        emerald_fish_match = re.search(emerald_fish_pattern, reply_message.embeds[0].description)

        self.data["balance"] = int(money_match.group(1).replace(",", "") if money_match else 0)
        self.data["clan"] = clan_match.group(1) if clan_match else ""
        self.data["biome"] = biome_match.group(1) if biome_match else ""
        self.data["gold_fish"] = int(gold_fish_match.group(1).replace(",", "") if gold_fish_match else self.data["gold_fish"])
        self.data["emerald_fish"] = int(emerald_fish_match.group(1).replace(",", "") if emerald_fish_match else self.data["emerald_fish"])


        notif = {
            "title": "Virtual Fisher Data Update",
            "data": {
                "clan": self.data["clan"],
                "biome": self.data["biome"],
                "gold_fish": self.data["gold_fish"],
                "emerald_fish": self.data["emerald_fish"],
                "money": self.data["balance"],
                "trips": self.data["trips"]
            },
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.bot.telegram_notif.send_message(f"```json\n{json.dumps(notif, indent=4)}\n```")
        await self.bot.database.execute("UPDATE virtualfisher SET balance = %s, clan = %s, biome = %s, gold_fish = %s, emerald_fish = %s WHERE user_id = %s",
                                        (
                                            self.data["balance"],
                                            self.data["clan"],
                                            self.data["biome"],
                                            self.data["gold_fish"],
                                            self.data["emerald_fish"],
                                            self.bot.user.id
                                        ))

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if (not message.guild and
                message.author.id == self.bot.owner.id and
                message.content.startswith(self.bot.command_prefix)):
            parts = message.content[1:].split()
            command_name = parts[0]
            if command_name == "verify":
                code = parts[1] if len(parts) > 1 else ""
                await self.verify_command.__call__(self.channel, answer=code)
                await self.fisher_tasks.start()
                await message.reply("Verification command sent. Fisher task will resume.")
            else:
                return

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(1)
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