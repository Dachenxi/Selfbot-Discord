import os
import asyncio
import discord
from dotenv import load_dotenv
from modules import bot, setup_logging, setup_cogs, setup_events
from database.database import db

logger = setup_logging()
load_dotenv(".env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

async def run_bot():
    try:
        logger.info("Starting database Connection!")
        await db.connect()
        logger.info("Database connection established successfully!.")
        await setup_cogs()
        setup_events()
        if not DISCORD_TOKEN:
            logger.error("Discord token not found!")
            return
        await bot.start(token=DISCORD_TOKEN, reconnect=True)
    except discord.ClientException as e:
        logger.error(e)
        await bot.close()
        await asyncio.sleep(5)

def exception_handler(loop, context):
    exception = context.get("exception")
    if isinstance(exception, (asyncio.CancelledError, KeyboardInterrupt)) or 'KeyboardInterrupt' in str(context):
        logger.warning("The program is stopped by the user, the program will stop the bot.")
        loop.stop()
        return
    loop.default_exception_handler(context)

if __name__ == "__main__":
    event = asyncio.new_event_loop()
    asyncio.set_event_loop(event)
    event.set_exception_handler(exception_handler)
    try:
        event.run_until_complete(run_bot())
    except KeyboardInterrupt:
        pass
    finally:
        event.close()