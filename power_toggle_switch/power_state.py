from enum import Enum
import json
from power_toggle_switch.config import PowerToggleConfig
import logging

class State(str, Enum):
    NORMAL = 'NORMAL'
    SHUTDOWN = 'SHUTDOWN'


class PowerState():
    def __init__(self, config: PowerToggleConfig, logger: logging.Logger):
        self.config = config
        self.state: State = State.NORMAL
        self.logger = logger
    
    def set_state(self, state: State):
        self.state = state
        
    def get_state(self) -> State:
        return self.state
    
    def process_message(self, message: str) -> State:
        try:
            data = json.loads(message)
            state_value = data.get('state', '').lower()
            
            if state_value == 'shutdown':
                self.set_state(State.SHUTDOWN)
            elif state_value == 'normal':
                self.set_state(State.NORMAL)
        except (json.JSONDecodeError, KeyError):
            self.logger.error("Invalid message format or missing 'state' key " + message)
        
        return self.get_state()