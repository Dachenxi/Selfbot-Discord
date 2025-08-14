import re
import asyncio
import random
import logging
import os
from modules import Settings
from discord.ext import commands, tasks
from discord import Message, TextChannel, SlashCommand
from dotenv import load_dotenv

load_dotenv(".env")
logger = logging.getLogger(__name__)
settings = Settings()

class VirtualFisher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner = self.bot.get_user(int(os.getenv("OWNER_ID")))
        self.fish_counter = 0

    @tasks.loop(seconds=2)  # interval kecil; eksekusi utama dikendalikan sendiri
    async def fish(self,
                   channel: TextChannel,
                   fish_command: SlashCommand,
                   sell_command: SlashCommand):
        try:
            # Tunggu jika sedang pause
            await self._pause_event.wait()

            # Eksekusi fishing
            await fish_command.__call__(channel)
            self.fish_counter += 1

            # Setiap 10 kali jual
            if self.fish_counter % 10 == 0:
                await sell_command.__call__(channel, amount="all")

            # Delay acak antar cast
            delay = random.randint(60, 300)
            for _ in range(delay):
                # Jika dipause di tengah tidur, berhenti tidur lebih lanjut
                if not self._pause_event.is_set():
                    break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error occurred while fishing: {e}")
            await asyncio.sleep(5)

    @commands.command(name="startfishing")
    async def startfishing(self, ctx: commands.Context):
        self.channel_start = ctx.channel
        slash_commands = await ctx.channel.application_commands()
        fish_command = None
        sell_command = None

        for cmd in slash_commands:
            if cmd.id == settings.get("fish_command_id"):
                fish_command = cmd
            elif cmd.id == settings.get("sell_command_id"):
                sell_command = cmd

        if fish_command and sell_command:
            if self.fish.is_running():
                await ctx.channel.send("Fishing sudah berjalan.")
                return
            self._fish_args = (ctx.channel, fish_command, sell_command)
            self._fish_kwargs = {}
            self._pause_event.set()
            self.fish.start(*self._fish_args, **self._fish_kwargs)
            await ctx.channel.send("Mulai fishing.")
        else:
            await ctx.channel.send("Gagal menemukan perintah slash.")

    @commands.command(name="stopfishing")
    async def stopfishing(self, ctx: commands.Context):
        if self.fish.is_running():
            self.fish.stop()
            await ctx.channel.send("Dihentikan.")
        else:
            await ctx.channel.send("Tidak berjalan.")

    @commands.Cog.listener()
    async def on_message(self, ctx: Message):
        try:
            if (ctx.guild
                and ctx.guild.id == 950039010733076560
                and ctx.author.id == 574652751745777665
                and self.bot.user.name == ctx.interaction.user.name):

                for embed in ctx.embeds:
                    if not embed.description:
                        continue

                    title = embed.title or ""
                    desc_lower = embed.description.lower()

                    # Deteksi anti-bot
                    if "anti-bot" in title.lower() or "verify" in desc_lower:
                        # Pause otomatis di sini
                        if self._pause_event.is_set():
                            self._pause_event.clear()
                            logger.info("Fishing dipause otomatis karena verifikasi.")
                        slash_commands = await ctx.channel.application_commands()
                        verify_command = None
                        for command in slash_commands:
                            if command.id == 912432961222238220:
                                verify_command = command
                                break

                        if verify_command and "Code" in embed.description:
                            kode_verify = re.search(r"Code:\s*\*\*(\w+)\*\*", embed.description)
                            if kode_verify:
                                await verify_command.__call__(channel=ctx.channel, answer=kode_verify.group(1))
                                # Setelah berhasil kirim jawaban, resume
                                self._pause_event.set()
                                logger.info("Verifikasi selesai. Resume fishing.")
                        elif embed.image:
                            # Kirim ke owner untuk manual (tetap pause sampai owner intervensi)
                            if self.owner:
                                await ctx.forward(self.owner.dm_channel)
                        return

            elif ctx.channel.id == 873024435790176288:
                if ctx.content.startswith("verify"):
                    slash_commands = await self.channel_start.application_commands()
                    verify_command = None
                    for command in slash_commands:
                        if command.id == 912432961222238220:
                            verify_command = command
                            break

                    parts = ctx.content.split(None, 1)
                    if verify_command and len(parts) == 2 and parts[1].strip():
                        kode_verif = parts[1].strip()
                        await verify_command.__call__(channel=self.channel_start, answer=kode_verif)

                    # Setelah verifikasi manual, lanjutkan fishing bila ada
                    if self._fish_args:
                        if not self.fish.is_running():
                            self.fish.start(*self._fish_args, **self._fish_kwargs)
                        self._pause_event.set()
                        await self.channel_start.channel.send("Verifikasi selesai. Fishing dilanjutkan.")
                    else:
                        await self.channel_start.channel.send("Tidak ada sesi fishing untuk dilanjutkan.")
                    return


        except Exception as e:
            logger.error(f"on_message error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VirtualFisher(bot))
    logger.info("VirtualFisher command berhasil di load")