import logging
import discord
from discord.ext import commands
from database.database import db, Database
from .telegram import notif, Telegram

logger = logging.getLogger(__name__)

class Bot(commands.Bot):
    def __init__(
            self,
            database_conn: Database,
            telegram_notif: Telegram,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.database = database_conn
        self.telegram_notif = telegram_notif

    async def parse(self, message: discord.Message):
        if not message.guild:
            return

        if message.author.id == self.user.id:
            if message.content.startswith(self.command_prefix):
                try:
                    await message.delete()
                    parts = message.content[1:].split()
                    command_name = parts[0]
                    logger.info(f"Get Command With Command Name: {self.command_prefix}{command_name}")
                    await message.channel.typing()
                    command = self.get_command(command_name)
                    ctx = await self.get_context(message)
                    if command:
                        try:
                            args = parts[1] if len(parts) > 1 else ''
                            if args:
                                await command(ctx, args) # Although it is not the right type, it works.
                            else:
                                await command(ctx) # Although it is not the right type, it works.
                        except Exception as e:
                            logger.error(f"Receiving an error when attempting to send a command: {e}")
                    else:
                        await message.reply("There is no command with that name!")
                except Exception as e:
                    logger.info(f"Error when processing message. Message received {message.content} with error {e}")

    async def on_message(self, message):
        await self.parse(message)

    async def setup(self):
        """Get settings and check user from database"""

        user = await self.database.fetch("SELECT * FROM user WHERE user_id = %s", (self.user.id,))
        if not user:
            logger.warning("User not found in database, creating a new user entry.")
            await self.database.execute("INSERT INTO user (user_id, global_name) VALUES (%s, %s)", (self.user.id, self.user.display_name))

        setting = await self.database.fetch("SELECT owner_id, prefix, server_id FROM settings WHERE user_id = %s",
                                            (self.user.id,),
                                            one=True)
        if setting:
            self.command_prefix = setting["prefix"]
        else:
            logger.warning(f"Settings for user {self.user.display_name} not found in database, asking the user to input.")
            ask_owner_id = int(input("Please enter your Discord user ID to set as owner/main account: "))
            ask_server_id = int(input("Please enter your Main server ID to set as server ID\nYou can change it later: "))
            await self.database.execute("INSERT INTO settings (user_id, owner_id, server_id) VALUES (%s, %s, %s)", (self.user.id, ask_owner_id, ask_server_id))
            logger.warning(f"Prefix not found in settings, using default {self.command_prefix}, you can change it using {self.command_prefix}prefix <new_prefix> command.")


bot = Bot(
    command_prefix="!",
    database_conn=db,
    telegram_notif=notif,
    help_command=None,
    status=discord.Status.online,
)