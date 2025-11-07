import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from .config import MsuManagerConfig
from .controller import Controller
from .controller.messages import MsuControllerMessage
from .controller import MsuControllerProtocol

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


async def before_startup(app: FastAPI):
    CONFIG = MsuManagerConfig()
    app.state.CONFIG = CONFIG
    logger.info(f'Effective configuration: {CONFIG.model_dump_json(indent=2)}')

    logging.getLogger().setLevel(app.state.CONFIG.log_level.value)

    controller = Controller(CONFIG.msu_agent.shutdown_command, CONFIG.msu_agent.shutdown_delay_s)
    app.state.controller = controller

    agent_bind_address = CONFIG.msu_agent.udp_bind_address
    agent_listen_port = CONFIG.msu_agent.udp_listen_port
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: MsuControllerProtocol(controller=controller), local_addr=(agent_bind_address, agent_listen_port)
    )
    logger.info(f'Started MsuProtocol UDP listener on {agent_bind_address}:{agent_listen_port}')

    app.state.udp_transport = transport
    app.state.udp_protocol = protocol

async def after_shutdown(app: FastAPI):
    app.state.udp_transport.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await before_startup(app)
    yield
    await after_shutdown(app)

app = FastAPI(lifespan=lifespan)

@app.get('/health', status_code=status.HTTP_204_NO_CONTENT)
async def health():
    pass

@app.post('/command', status_code=status.HTTP_204_NO_CONTENT)
async def command_endpoint(command: MsuControllerMessage):
    logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
    await app.state.controller.process_command(command)