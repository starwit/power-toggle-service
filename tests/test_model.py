from pydantic_core import ValidationError

from msu_manager.controller.messages import (HeartbeatCommand, LogCommand,
                                             LogEntry, ShutdownCommand,
                                             validate_json_message,
                                             validate_python_message)


def test_shutdown_command_parsing():
    m = validate_python_message({
        'command': 'shutdown' 
    })
    assert isinstance(m, ShutdownCommand)
    assert m.command == 'shutdown'

def test_heartbeat_command_parsing():
    m = validate_python_message({
        'command': 'heartbeat',
        'version': '1.0.0'
    })
    assert isinstance(m, HeartbeatCommand)
    assert m.command == 'heartbeat'
    assert m.version == '1.0.0'

def test_log_command_parsing():
    m = validate_python_message({
        'command': 'log',
        'entries': [
            {'timestamp': '2025-01-01T00:00:00Z', 'level': 'info', 'message': 'Test log message'}
        ]
    })
    assert isinstance(m, LogCommand)
    assert m.command == 'log'
    assert m.entries[0] == LogEntry(timestamp='2025-01-01T00:00:00Z', level='info', message='Test log message')

def test_invalid_command_parsing():
    try:
        validate_python_message({
            'command': 'invalid_command'
        })
        assert False, "Expected validation error"
    except Exception as e:
        assert isinstance(e, ValidationError)
        assert "validation error" in str(e)

def test_json_parsing():
    m = validate_json_message('''
    {
        "command": "shutdown"
    }
    ''')
    assert isinstance(m, ShutdownCommand)
    assert m.command == 'shutdown'