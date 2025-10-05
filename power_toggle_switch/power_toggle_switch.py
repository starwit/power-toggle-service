import logging
import time
import signal
import threading
from power_toggle_switch.config import PowerToggleConfig
import socket

logger = logging.getLogger(__name__)

def run_stage():

    stop_event = threading.Event()

    # Register signal handlers
    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    CONFIG = PowerToggleConfig()
    logging.basicConfig(level=CONFIG.log_level.value, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(CONFIG.log_level.value)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CONFIG.bind_address, CONFIG.udp_port))
    sock.settimeout(1.0)  # 1 second timeout

    try:
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                print(f"Received packet from {addr}: {data.decode('utf-8')}")
            except socket.timeout:
                continue  # Check stop_event again
    finally:
        sock.close()