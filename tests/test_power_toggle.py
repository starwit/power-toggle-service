import pytest
from power_toggle_switch.config import PowerToggleConfig

def test_config():
    CONFIG = PowerToggleConfig()
    assert CONFIG.udp_port != None