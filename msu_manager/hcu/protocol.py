import asyncio
import json
import logging
from json import JSONDecodeError
from typing import Tuple

from .controller import HcuController
from .messages import validate_python_message

logger = logging.getLogger(__name__)


class HcuProtocol(asyncio.DatagramProtocol):
    def __init__(self, controller: HcuController = None):
        self._controller = controller
        self._transport = None
        
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self._transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        logger.debug(f'Received UDP packet from {addr}: {data}')

        try:
            json_dict = json.loads(data.strip())
        except (UnicodeDecodeError, JSONDecodeError):
            logger.error(f'Failed to decode UDP packet from {addr}: {data}', exc_info=True)
            return
        
        command = validate_python_message(json_dict)
        logger.debug(f'Received {type(command).__name__} via UDP: {command.model_dump_json(indent=2)}')

        if self._controller:
            asyncio.create_task(self._controller.process_command(command))

    def connection_lost(self, exc):
        logger.info('HcuProtocol UDP listener stopped', exc_info=exc)
