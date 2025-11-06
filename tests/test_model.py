from msu_manager.model import validate_python_message, StartCommand

def test_message_parsing():
    m = validate_python_message({
        'command': 'start', 
        'target_id': 'test_id'
    })
    assert isinstance(m, StartCommand)