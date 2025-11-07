from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class CommandType(StrEnum):
    SHUTDOWN = "SHUTDOWN"
    RESUME = "RESUME"
    HEARTBEAT = "HEARTBEAT"
    LOG = "LOG"


class ShutdownCommand(BaseModel):
    command: Literal[CommandType.SHUTDOWN]


class ResumeCommand(BaseModel):
    command: Literal[CommandType.RESUME]


class HeartbeatCommand(BaseModel):
    command: Literal[CommandType.HEARTBEAT]
    version: str | None = None


class LogCommand(BaseModel):
    command: Literal[CommandType.LOG]
    key: str
    value: str


# Discriminated union using the 'command' field
MsuControllerMessage = Annotated[
    Union[
        ShutdownCommand,
        ResumeCommand,
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