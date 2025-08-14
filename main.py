import os
import asyncio
import discord
from dotenv import load_dotenv
from modules import bot, setup_logging, setup_cogs

logger = setup_logging()
load_dotenv(".env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

async def run_bot():
    try:
        await setup_cogs()
        if not DISCORD_TOKEN:
            logger.error("Discord token not found!")
            return
        await bot.start(token=DISCORD_TOKEN, reconnect=True)
    except discord.ClientException as e:
        logger.error(e)
        await bot.close()
        await asyncio.sleep(5)

async def stop_bot():
    await bot.change_presence(status=discord.Status.offline)
    await bot.close()
    logger.warning("Bot stopped")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        loop.run_until_complete(stop_bot())
        logger.warning("The program is stopped by the user, the program will stop the bot.")
    finally:
        loop.close()