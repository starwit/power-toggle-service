from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class CommandType(StrEnum):
    START = "start"
    STOP = "stop"
    STATUS = "status"
    CONFIG = "config"


class StartCommand(BaseModel):
    command: Literal[CommandType.START]
    target_id: str
    params: dict | None = None


class StopCommand(BaseModel):
    command: Literal[CommandType.STOP]
    target_id: str
    force: bool = False


class StatusCommand(BaseModel):
    command: Literal[CommandType.STATUS]
    target_id: str | None = None


class ConfigCommand(BaseModel):
    command: Literal[CommandType.CONFIG]
    key: str
    value: str | int | bool


# Discriminated union using the 'command' field
MsuControllerMessage = Annotated[
    Union[
        StartCommand,
        StopCommand,
        StatusCommand,
        ConfigCommand,
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