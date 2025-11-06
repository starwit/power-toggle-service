from pydantic import BaseModel


class MsuControllerMessage(BaseModel):
    command: str