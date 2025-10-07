import pytest
from msu_manager.config import PowerToggleConfig

def test_config():
    CONFIG = PowerToggleConfig()
    assert CONFIG.udp_port != None