from pydantic import BaseModel


class Event(BaseModel):
    id: str
    type: str
    source_interface: str
    destination_ip: str
    count: int
    timeout: int
