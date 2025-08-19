import logging
from modules import bot

logger = logging.getLogger(__name__)


def setup_events():
    logger.info("Setting up events")

    @bot.event
    async def on_ready():
        await bot.setup()
        logger.info(f"Bot is ready, prefix is set to: {bot.command_prefix}")
