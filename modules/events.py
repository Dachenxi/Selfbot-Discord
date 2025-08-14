from .bot import bot
import logging

logger = logging.getLogger(__name__)

def setup_events():
    logger.info("Setting up events")
    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user.name}")
        logger.info(f"Prefix bot is: {bot.setting.get('prefix')}")
