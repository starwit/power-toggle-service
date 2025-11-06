import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Tuple

from fastapi import FastAPI, status

from .config import MsuManagerConfig
from .model import validate_json_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class MsuControllerProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport
        logger.info(f'Started MsuProtocol UDP listener on {app.state.CONFIG.udp_bind_address}:{app.state.CONFIG.udp_listen_port}')

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        logger.debug(f'Received UDP packet from {addr}: {data}')

        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            logger.error(f'Failed to decode UDP packet from {addr}: not valid UTF-8')
            return

        logger.debug(f'Received command: {validate_json_message(text).model_dump_json(indent=2)}')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This (until yield) is run before startup
    CONFIG = MsuManagerConfig()
    app.state.CONFIG = CONFIG
    logger.info(f'Effective configuration: {CONFIG.model_dump_json(indent=2)}')

    logging.getLogger().setLevel(app.state.CONFIG.log_level.value)

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: MsuControllerProtocol(), local_addr=(CONFIG.udp_bind_address, CONFIG.udp_listen_port)
    )
    app.state.udp_transport = transport
    app.state.udp_protocol = protocol

    yield

    # This is run after shutdown
    app.state.udp_transport.close()

app = FastAPI(lifespan=lifespan)

@app.get('/health', status_code=status.HTTP_204_NO_CONTENT)
def health():
    pass