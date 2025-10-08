import logging
import signal
import socket
import threading
import subprocess
from msu_manager.config import PowerToggleConfig
from msu_manager.application_state import ApplicationState, PowerState

logger = logging.getLogger(__name__)

def run_stage():
    CONFIG = PowerToggleConfig()
    logging.basicConfig(level=CONFIG.log_level.value, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(CONFIG.log_level.value)
    
    app_state = ApplicationState(CONFIG, logger)

    stop_event = threading.Event()
    # Catch termination signals to ensure graceful shutdown
    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        app_state.set_power_state(PowerState.NORMAL)
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CONFIG.bind_address, CONFIG.udp_port))
    sock.settimeout(1.0)  # 1 second timeout

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