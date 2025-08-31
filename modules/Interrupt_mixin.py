import asyncio
import logging
from discord.ext import tasks

logger = logging.getLogger("InterruptMixin Modules")

class TaskInterruptMixin:
    def __init__(self, *args, **kwargs):
        self._interrupt_event = asyncio.Event()
        super().__init__(*args, **kwargs)

    async def interruptible_wait(self, delay: float) -> bool:
        try:
            await asyncio.wait_for(self._interrupt_event.wait(), timeout=delay)
            return True
        except asyncio.TimeoutError:
            return False

    def interrupt(self, task: tasks.Loop):
        logger.warning(f"Interrupting task: {task.coro.__name__}")
        self._interrupt_event.set()
        task.cancel()

    def clear_interrupt(self):
        self._interrupt_event.clear()
