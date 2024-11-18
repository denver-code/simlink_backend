from dataclasses import dataclass


@dataclass
class PingResult:
    sequence: int
    success: bool
    rtt: float
    source_mac: str
    dest_mac: str
    source_ip: str
    dest_ip: str
    ttl: int = 64


@dataclass
class ARPEntry:
    ip: str
    mac: str
    timestamp: float
    is_complete: bool = False
