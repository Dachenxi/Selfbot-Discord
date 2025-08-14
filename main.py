import os
import asyncio
import discord
from dotenv import load_dotenv
from modules import bot, setup_logging, setup_cogs, setup_events

logger = setup_logging()
load_dotenv(".env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

async def run_bot():
    try:
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

async def stop_bot():
    await bot.change_presence(status=discord.Status.offline)
    await bot.close()
    logger.warning("Bot stopped")


async def cleanup_tasks():
    """Cancel all pending tasks except the current one"""
    current_task = asyncio.current_task()
    tasks = [task for task in asyncio.all_tasks() if task is not current_task]

    if tasks:
        logger.info(f"Cancelling {len(tasks)} pending tasks...")
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All pending tasks cancelled.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.warning("The program is stopped by the user, the program will stop the bot.")
        loop.run_until_complete(stop_bot())
        logger.warning("The program will clean up tasks now.")
        loop.run_until_complete(cleanup_tasks())
    finally:
        loop.close()