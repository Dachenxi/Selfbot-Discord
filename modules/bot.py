import logging
import discord
from discord.ext import commands
from discord import Message
from .settings import Settings

logger = logging.getLogger(__name__)
prefix = "!"


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setting = Settings()

    async def on_message(self, context: Message):
        if not context.guild:
            return

        if context.author.id == self.user.id:
            if context.content.startswith(prefix):
                try:
                    await context.delete()
                    parts = context.content[1:].split()
                    command_name = parts[0]
                    logger.info(f"Get Command With Command Name: !{command_name}")
                    await context.channel.typing()
                    command = self.get_command(command_name)
                    if command:
                        try:
                            args = parts[1] if len(parts) > 1 else ''
                            if args:
                                await command(context, args) # Although it is not the right type, it works.
                            else:
                                await command(context) # Although it is not the right type, it works.
                        except Exception as e:
                            logger.info(f"Receiving an error when attempting to send a command: {e}")
                    else:
                        await context.reply("There is no command with that name!")
                except Exception as e:
                    logger.info(f"Error when processing message. Message received {context.content} with error {e}")


bot = Bot(
    command_prefix=prefix,
    help_command=None,
    status=discord.Status.online,
)
