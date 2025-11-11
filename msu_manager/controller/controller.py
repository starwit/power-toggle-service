import asyncio
import logging
from typing import List

from .messages import (HeartbeatCommand, LogCommand, MsuControllerMessage,
                       ResumeCommand, ShutdownCommand)

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, shutdown_command: List[str], shutdown_delay_s: int):
        self.shutdown_command = shutdown_command
        self.shutdown_delay_s = shutdown_delay_s
        self._shutdown_task = None

    async def process_command(self, command: MsuControllerMessage):
        logger.info(f'Processing {type(command).__name__}')
        match command:
            case ShutdownCommand():
                await self.handle_shutdown()
            case ResumeCommand():
                await self.handle_resume()
            case HeartbeatCommand():
                pass
            case LogCommand():
                logger.info(f'LOG - {command.key}: {command.value}')
                
    async def handle_shutdown(self):
        if self._shutdown_task is not None:
            logger.warning('Shutdown already scheduled, ignoring duplicate request.')
            return
        
        logger.info(f'Scheduling shutdown in {self.shutdown_delay_s} seconds.')
        self._shutdown_task = asyncio.create_task(self._delayed_shutdown())

    async def handle_resume(self):
        if self._shutdown_task is None:
            logger.warning('No shutdown scheduled, nothing to resume.')
            return
        
        logger.info('Cancelling scheduled shutdown.')
        await self._cancel_shutdown()
        logger.info('Scheduled shutdown cancelled successfully.')

    async def _cancel_shutdown(self):
        if self._shutdown_task is not None:
            self._shutdown_task.cancel()
            try:
                await self._shutdown_task
            except asyncio.CancelledError:
                # Task cancellation is expected here as we've called cancel()
                pass
            self._shutdown_task = None
        
    async def _delayed_shutdown(self):
        await asyncio.sleep(self.shutdown_delay_s)
        
        logger.info('Executing shutdown now.')
        proc = await asyncio.create_subprocess_exec(*self.shutdown_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()

        # This is probably never reached if shutdown is successful
        if proc.returncode != 0:
            logger.error(f'Shutdown command failed with exit code {proc.returncode}')
            if stdout:
                logger.error(f'[stdout]\n{stdout.decode()}')
            if stderr:
                logger.error(f'[stderr]\n{stderr.decode()}')
            await self._cancel_shutdown()