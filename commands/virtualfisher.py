import re
import asyncio
import random
import logging
from modules import SelfBot
from discord.ext import commands, tasks
from discord import Message, TextChannel, SlashCommand

logger = logging.getLogger(__name__)


# noinspection PyTypeChecker
class VirtualFisher(commands.Cog):
    channel: TextChannel
    slash_commands: SlashCommand
    verify_command: SlashCommand
    sell_command: SlashCommand
    fish_command: SlashCommand
    verify_command: SlashCommand

    def __init__(self, bot: SelfBot):
        self.bot = bot
        self.owner = self.bot.get_user(bot.setting.get("owner_id"))
        self.fish_counter = 0
        self.delay_fish = 0
        self.channel = None
        self.slash_commands = None
        self.sell_command = None
        self.fish_command = None
        self.verify_command = None

    @tasks.loop(seconds=2)  # small intervals because they are handled directly by the function
    async def fish_task(self):
        try:
            await self.fish_command.__call__(self.channel)
            self.fish_counter += 1
            if self.fish_counter % 15 == 0: # Sell after fishing 15 times
                await self.sell_command.__call__(self.channel, amount="all")
            self.delay_fish = random.randint(60, 600)
            await asyncio.sleep(self.delay_fish)
        except Exception as e:
            logger.error(f"Error occurred while fishing: {e}")
            await asyncio.sleep(5)

    async def _initialize_fishing_commands(self, channel):
        """Initialize fishing and sell commands"""
        if self.channel is None:
            self.channel = channel

        if self.slash_commands is None:
            self.slash_commands = await channel.application_commands()

        if self.sell_command is None or self.fish_command is None:
            for cmd in self.slash_commands:
                if cmd.id == 912432960643416115:  # Fish commands id
                    self.fish_command = cmd
                elif cmd.id == 912432960643416116:  # sell command id
                    self.sell_command = cmd

    @commands.command(name="startfishing")
    async def startfishing(self, ctx: commands.Context):
        await self._initialize_fishing_commands(ctx.channel)

        if not (self.fish_command and self.sell_command):
            await ctx.channel.send("Failed to find slash command.")
            return

        if self.fish_task.is_running():
            await ctx.channel.send("There is already a fishing task in progress.")
            return

        await self.fish_task.start()
        await ctx.channel.send("start fishing", delete_after=10)

    @commands.command(name="stopfishing")
    async def stopfishing(self, ctx: commands.Context):
        if self.fish_task.is_running():
            self.fish_task.cancel()
            await ctx.channel.send("Stop fishing")
        else:
            await ctx.channel.send("Fishing task not running")

    async def _ensure_slash_commands(self, channel):
        """Ensure slash commands are loaded"""
        if self.slash_commands is None:
            self.slash_commands = await channel.application_commands()

        if self.verify_command is None:
            for command in self.slash_commands:
                if command.id == 912432961222238220:
                    self.verify_command = command
                    break

    async def _handle_antibot_verification(self, ctx: Message, embed):
        """Handle anti-bot verification process"""
        # Stop fishing task
        if self.fish_task.is_running():
            self.fish_task.cancel()
            logger.info("Terminate fish task because there is anti bot")

        await self._ensure_slash_commands(ctx.channel)

        # Auto-solve text verification
        if self.verify_command and "Code" in embed.description:
            kode_verify = re.search(r"Code:\s*\*\*(\w+)\*\*", embed.description)
            if kode_verify:
                await self.verify_command.__call__(channel=ctx.channel, answer=kode_verify.group(1))
                logger.info("Verifikasi selesai. Resume fishing.")
                await self.fish_task.start()
                return

        # Handle image captcha
        if embed.image and self.owner:
            await ctx.forward(self.owner)
            await self.owner.send("Please solve the captcha with message, `verify <code>`")

    async def _handle_bot_message(self, ctx: Message):
        """Handle messages from Virtual Fisher bot"""
        for embed in ctx.embeds:
            if not embed.description:
                continue

            title = embed.title or ""
            desc_lower = embed.description.lower()

            # Check for anti-bot verification
            if "anti-bot" in title.lower() or "verify" in desc_lower:
                await self._handle_antibot_verification(ctx, embed)
                return

    async def _handle_owner_verify_command(self, ctx: Message):
        """Handle verify command from owner"""
        await self._ensure_slash_commands(ctx.channel)

        parts = ctx.content.split(None, 1)
        if not (self.verify_command and len(parts) == 2 and parts[1].strip()):
            await self.channel.send("No fishing session to continue.")
            return

        kode_verif = parts[1].strip()
        await self.verify_command.__call__(channel=self.channel, answer=kode_verif)

        if self.fish_task.is_running():
            await self.owner.send("Fish task is still running")
        else:
            await self.channel.send("Verification complete. Fishing resumed.")
            await self.fish_task.start()

    def _is_virtual_fisher_message(self, ctx: Message) -> bool:
        """Check if message is from Virtual Fisher in correct guild"""
        return (
            ctx.guild is not None
            and ctx.guild.id == 950039010733076560
            and ctx.author is not None
            and ctx.author.id == 574652751745777665
            and self.bot.user.name == ctx.interaction.user.name
        )

    def _is_owner_verify_message(self, ctx: Message) -> bool:
        """Check if message is verify command from owner"""
        return (
            ctx.author is not None
            and self.owner is not None
            and ctx.author.id == self.owner.id
            and ctx.content is not None
            and ctx.content.startswith("verify")
        )

    @commands.Cog.listener()
    async def on_message(self, ctx: Message):
        try:
            if self._is_virtual_fisher_message(ctx):
                await self._handle_bot_message(ctx)
            elif self._is_owner_verify_message(ctx):
                await self._handle_owner_verify_command(ctx)

        except Exception as e:
            logger.error(f"on_message error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VirtualFisher(bot))
    logger.info("VirtualFisher command successfully loaded")