import asyncio
import logging

from .messages import (HeartbeatCommand, LogCommand, MsuControllerMessage,
                       ShutdownCommand)

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self):
        pass

    async def process_command(self, command: MsuControllerMessage):
        logger.info(f'Processing {type(command).__name__}')
        match command:
            case ShutdownCommand():
                # await asyncio.create_subprocess_exec('sudo shutdown -h now')
                await self.handle_shutdown()
            case HeartbeatCommand():
                pass
            case LogCommand():
                for entry in command.entries:
                    logger.info(f'Log Entry - Timestamp: {entry.timestamp}, Level: {entry.level}, Message: {entry.message}')

    async def handle_shutdown(self):
        logger.info("Handling shutdown.")
        proc = await asyncio.create_subprocess_exec('touch', '/home/florian/Desktop/shutdown_executed')
        stdout, stderr = await proc.communicate()