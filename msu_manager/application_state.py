from enum import Enum
import json
from msu_manager.config import MsuManagerConfig
import logging

class ProtocolCommands(str, Enum):
    SHUTDOWN = 'SHUTDOWN'
    RESUME = 'RESUME'
    HEARTBEAT = 'HEARTBEAT'
    LOG = 'LOG'

class PowerState(str, Enum):
    NORMAL = 'NORMAL'
    SHUTDOWN = 'SHUTDOWN'

class ApplicationState():
    def __init__(self, config: MsuManagerConfig, logger: logging.Logger):
        self.config = config
        self.power_state: PowerState = PowerState.NORMAL
        self.logger = logger
    
    def set_power_state(self, state: PowerState):
        self.power_state = state
        
    def get_power_state(self) -> PowerState:
        return self.power_state
    
    def process_message(self, message: str) -> PowerState:
        try:
            data = json.loads(message)
            state_value = data.get('command', '').upper()
            self.logger.debug(f"Received command: {state_value}")

            match state_value:
                case ProtocolCommands.SHUTDOWN.value:
                    self.set_power_state(PowerState.SHUTDOWN)
                case ProtocolCommands.RESUME.value:
                    self.set_power_state(PowerState.NORMAL)
                    self.logger.info("Recevied resume command, resuming normal operation")
                case ProtocolCommands.HEARTBEAT.value:
                    self.logger.info("Heartbeat received " + data.get('version', ''))
                case ProtocolCommands.LOG.value:
                    self.logger.info(create_log_message(data))
                case _:
                    self.logger.error("Unknown command received: " + state_value)

        except (json.JSONDecodeError, KeyError):
            self.logger.error("Invalid message format or missing 'state' key " + message)
        
        return self.get_power_state()


def create_log_message(data) -> str:
    try:
        if 'values' in data:
            log_entries = [f"{item['key']}:{item['value']}" for item in data['values'] if 'key' in item and 'value' in item]
            return "; ".join(log_entries)
        else:
            return "LOG Invalid log format"
    except (json.JSONDecodeError, KeyError):
        return "LOG Invalid JSON format"