import logging
import signal
import socket
import threading
import subprocess
from msu_manager.config import PowerToggleConfig
from msu_manager.power_state import PowerState, State

logger = logging.getLogger(__name__)

def run_stage():
    CONFIG = PowerToggleConfig()
    logging.basicConfig(level=CONFIG.log_level.value, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(CONFIG.log_level.value)
    
    power_state = PowerState(CONFIG, logger)

    stop_event = threading.Event()

    # Register signal handlers
    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        power_state.set_state(State.NORMAL)
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
                power_state.process_message(data.decode('utf-8'))
                if power_state.get_state() == State.SHUTDOWN:
                    logger.info("Shutting down in %s seconds", CONFIG.shutdown_delay)
                    threading.Timer(CONFIG.shutdown_delay, lambda: stop_event.set()).start()
            except socket.timeout:
                continue  # Check stop_event again
        shutdown_server(power_state)
    finally:
        sock.close()
        
def shutdown_server(power_state):
    if power_state.get_state() == State.NORMAL:
        logger.info("Stop service without powering off server")
    if power_state.get_state() == State.SHUTDOWN:
        logger.info("Powering off server")
        subprocess.run(["sudo", "shutdown", "-h", "+1"])