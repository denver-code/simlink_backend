from pydantic import BaseModel
from typing import Optional, List


class NetworkCard(BaseModel):
    name: str
    mac: str
    speed: str


class Hardware(BaseModel):
    network_card: NetworkCard


class Interface(BaseModel):
    id: str
    name: str
    type: str
    mac: str
    ip: str
    subnet_mask: str
    gateway: str
    dns: List[str]
    status: str


class PC(BaseModel):
    id: str
    type: str
    name: str
    hardware: Hardware
    interfaces: List[Interface]
