import logging
import signal
import socket
import threading
import subprocess
from msu_manager.config import MsuManagerConfig
from msu_manager.application_state import ApplicationState, PowerState

logger = logging.getLogger(__name__)

def run_stage():
    logging.basicConfig(level=CONFIG.log_level.value, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(CONFIG.log_level.value)
    
    app_state = ApplicationState(CONFIG, logger)


    try:
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                logger.debug(f"Received message: {data.decode('utf-8')} from {addr}")
                app_state.process_message(data.decode('utf-8'))
                if app_state.get_power_state() == PowerState.SHUTDOWN:
                    logger.info("Shutting down in %s seconds", CONFIG.shutdown_delay)
                    threading.Timer(CONFIG.shutdown_delay, lambda: stop_event.set()).start()
            except socket.timeout:
                continue  # Check stop_event again
        shutdown_server(app_state)
    finally:
        sock.close()
        
def shutdown_server(app_state):
    if app_state.get_power_state() == PowerState.NORMAL:
        logger.info("Stop service without powering off server")
    if app_state.get_power_state() == PowerState.SHUTDOWN:
        logger.info("Powering off server")
        subprocess.run(["sudo", "shutdown", "-h", "+1"])