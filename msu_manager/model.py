from enum import StrEnum
from typing import Annotated, Literal, Union, List

from pydantic import BaseModel, Field, TypeAdapter


class CommandType(StrEnum):
    SHUTDOWN = "shutdown"
    HEARTBEAT = "heartbeat"
    LOG = "log"


class ShutdownCommand(BaseModel):
    command: Literal[CommandType.SHUTDOWN]


class HeartbeatCommand(BaseModel):
    command: Literal[CommandType.HEARTBEAT]
    version: str | None = None


class LogEntry(BaseModel):
    timestamp: str | None
    level: str | None
    message: str


class LogCommand(BaseModel):
    command: Literal[CommandType.LOG]
    entries: List[LogEntry]


# Discriminated union using the 'command' field
MsuControllerMessage = Annotated[
    Union[
        ShutdownCommand,
        HeartbeatCommand,
        LogCommand
    ],
    Field(discriminator='command')
]


# Some helper functions for explicitly parsing messages
_message_adapter = TypeAdapter(MsuControllerMessage)

def validate_python_message(data: dict) -> MsuControllerMessage:
    """Parse and validate a message dictionary into the appropriate command type."""
    return _message_adapter.validate_python(data)

def validate_json_message(data: str) -> MsuControllerMessage:
    """Parse and validate a JSON string message into the appropriate command type."""
    return _message_adapter.validate_json(data)