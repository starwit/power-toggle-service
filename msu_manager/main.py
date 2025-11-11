import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .config import MsuManagerConfig
from .controller import Controller, MsuControllerProtocol
from .controller.messages import MsuControllerMessage
from .uplink.monitor import UplinkMonitor

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

    if CONFIG.msu_controller.enabled:
        controller = Controller(CONFIG.msu_controller.shutdown_command, CONFIG.msu_controller.shutdown_delay_s)
        app.state.controller = controller

        controller_bind_address = CONFIG.msu_controller.udp_bind_address
        controller_listen_port = CONFIG.msu_controller.udp_listen_port
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: MsuControllerProtocol(controller=controller), local_addr=(controller_bind_address, controller_listen_port)
        )
        app.state.controller_transport = transport
        app.state.controller_protocol = protocol

        logger.info(f'Started MsuProtocol UDP listener on {controller_bind_address}:{controller_listen_port}')

    if CONFIG.uplink_monitor.enabled:
        uplink_monitor = UplinkMonitor(CONFIG.uplink_monitor)
        app.state.uplink_monitor = uplink_monitor
        app.state.uplink_monitor_task = asyncio.create_task(uplink_monitor.run())

        logger.info('Started UplinkMonitor')

async def after_shutdown(app: FastAPI):
    if app.state.CONFIG.msu_controller.enabled:
        app.state.controller_transport.close()

    if app.state.CONFIG.uplink_monitor.enabled:
        app.state.uplink_monitor_task.cancel()
        try:
            await app.state.uplink_monitor_task
        except asyncio.CancelledError:
            # Task cancellation is expected here as we've called cancel()
            pass
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    await before_startup(app)
    yield
    await after_shutdown(app)

app = FastAPI(lifespan=lifespan)

@app.get('/health', status_code=status.HTTP_204_NO_CONTENT)
async def health():
    pass

@app.post('/controller/command', status_code=status.HTTP_204_NO_CONTENT, responses={404: {}})
async def command_endpoint(command: MsuControllerMessage):
    logger.info(f'Received {type(command).__name__} via HTTP: {command.model_dump_json(indent=2)}')
    if not app.state.CONFIG.msu_controller.enabled:
        logger.warning('MsuController is disabled; ignoring command')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='MsuController is disabled')

    await app.state.controller.process_command(command)