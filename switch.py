from pydantic import BaseModel
from typing import Optional, List


class NetworkCard(BaseModel):
    name: str
    mac: str
    speed: str


class Hardware(BaseModel):
    network_card: NetworkCard


class SwitchInterface(BaseModel):
    id: str
    name: str
    type: str
    status: str
    connected_to: Optional[str]


class Switch(BaseModel):
    id: str
    type: str
    name: str

    hardware: Hardware
    interfaces: List[SwitchInterface]
