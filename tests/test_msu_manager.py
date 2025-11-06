import pytest
from msu_manager.config import MsuManagerConfig

def test_config():
    CONFIG = MsuManagerConfig()
    assert CONFIG.udp_port != None