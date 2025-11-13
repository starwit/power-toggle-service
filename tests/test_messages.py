import pytest
from pydantic_core import ValidationError

from msu_manager.hcu.messages import (HeartbeatCommand, LogCommand,
                                             ResumeCommand, ShutdownCommand,
                                             validate_json_message,
                                             validate_python_message)


def test_shutdown_command_parsing():
    m = validate_python_message({
        'command': 'SHUTDOWN' 
    })
    assert isinstance(m, ShutdownCommand)
    assert m.command == 'SHUTDOWN'

def test_resume_command_parsing():
    m = validate_python_message({
        'command': 'RESUME' 
    })
    assert isinstance(m, ResumeCommand)
    assert m.command == 'RESUME'

def test_heartbeat_command_parsing():
    m = validate_python_message({
        'command': 'HEARTBEAT',
        'version': '1.0.0'
    })
    assert isinstance(m, HeartbeatCommand)
    assert m.command == 'HEARTBEAT'
    assert m.version == '1.0.0'

def test_log_command_parsing():
    m = validate_python_message({
        'command': 'LOG',
        'key': 'test_key',
        'value': 'test_value'
    })
    assert isinstance(m, LogCommand)
    assert m.command == 'LOG'
    assert m.key == 'test_key'
    assert m.value == 'test_value'

def test_invalid_command_parsing():
    with pytest.raises(ValidationError):
        validate_python_message({
            'command': 'invalid_command'
        })

def test_json_parsing():
    m = validate_json_message('''
    {
        "command": "SHUTDOWN"
    }
    ''')
    assert isinstance(m, ShutdownCommand)
    assert m.command == 'SHUTDOWN'