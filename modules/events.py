import logging
from modules import bot

logger = logging.getLogger(__name__)


def setup_events():
    logger.info("Setting up events")

    @bot.event
    async def on_ready():
        idle_miner_cog = bot.get_cog("IdleMiner")
        if idle_miner_cog:
            await idle_miner_cog.idle_miner_setup()

        virtual_fisher_cog = bot.get_cog("VirtualFisher")
        if virtual_fisher_cog:
            await virtual_fisher_cog.virtual_fisher_setup()
        await bot.setup()
        logger.info(f"Bot is ready, prefix is set to: {bot.command_prefix}")
