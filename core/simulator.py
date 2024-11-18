from datetime import datetime
from core.utils import *
import random
import ipaddress
import time
from typing import Dict, List, Optional, Tuple
from models.packets import *
from models.connection import *
from models.event import *
from models.pc import *
from models.switch import *


class NetworkSimulator:
    def __init__(self, devices: Dict, connections: List[Connection]):
        self.devices = devices
        self.connections = connections
        self.arp_table: Dict[str, Dict[str, ARPEntry]] = (
            {}
        )  # device_id -> {ip -> ARPEntry}
        self.mtu = 1500
        self.initialize_arp_tables()

    def initialize_arp_tables(self):
        """Initialize empty ARP tables for each device"""
        for device_id in self.devices:
            self.arp_table[device_id] = {}

    def get_interface_by_ip(self, ip: str) -> Optional[Tuple[str, Interface]]:
        """Find device and interface that owns an IP address"""
        for device_id, device in self.devices.items():
            for interface in device.interfaces:
                if interface.ip == ip:
                    return device_id, interface
        return None

    def are_in_same_subnet(self, ip1: str, ip2: str, subnet_mask: str) -> bool:
        """Check if two IPs are in the same subnet"""
        net1 = ipaddress.IPv4Network(f"{ip1}/{subnet_mask}", strict=False)
        net2 = ipaddress.IPv4Network(f"{ip2}/{subnet_mask}", strict=False)
        return net1.network_address == net2.network_address

    def resolve_arp(
        self, source_device_id: str, source_interface: Interface, target_ip: str
    ) -> Optional[str]:
        """Simulate ARP resolution process"""
        # Check ARP cache first
        if (
            target_ip in self.arp_table[source_device_id]
            and self.arp_table[source_device_id][target_ip].is_complete
        ):
            return self.arp_table[source_device_id][target_ip].mac

        # Send ARP request
        target_device = self.get_interface_by_ip(target_ip)
        if not target_device:
            return None

        target_device_id, target_interface = target_device

        # Simulate ARP request
        arp_request_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "arp_request",
            "source_mac": source_interface.mac,
            "source_ip": source_interface.ip,
            "target_ip": target_ip,
        }

        # Simulate ARP response
        self.arp_table[source_device_id][target_ip] = ARPEntry(
            ip=target_ip,
            mac=target_interface.mac,
            timestamp=time.time(),
            is_complete=True,
        )

        arp_reply_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "arp_reply",
            "source_mac": target_interface.mac,
            "source_ip": target_ip,
            "target_mac": source_interface.mac,
            "target_ip": source_interface.ip,
        }

        return target_interface.mac

    def simulate_ping(self, event: Event) -> dict:
        """Simulate a ping operation with detailed logging"""
        logs = []
        success_count = 0
        rtts = []

        # Find source device and interface
        source_device_id = netid_to_id(event.source_interface)
        source_device = self.devices[source_device_id]
        source_interface = next(
            i
            for i in source_device.interfaces
            if f"{source_device_id}.{i.name}" == event.source_interface
        )

        # Initial validation
        if not source_interface:
            return self.create_error_log(event.id, "Source interface not found")

        # Find destination device
        dest_device = self.get_interface_by_ip(event.destination_ip)
        if not dest_device:
            return self.create_error_log(event.id, "Destination IP not reachable")

        dest_device_id, dest_interface = dest_device

        # ARP Resolution
        dest_mac = self.resolve_arp(
            source_device_id, source_interface, event.destination_ip
        )
        if not dest_mac:
            return self.create_error_log(event.id, "ARP resolution failed")

        # Simulate ping packets
        for seq in range(event.count):
            start_time = time.time()

            # Simulate network latency and packet loss
            packet_lost = random.random() < 0.01  # 1% packet loss
            rtt = random.uniform(0.1, 2.0)  # RTT between 0.1ms and 2ms

            if not packet_lost:
                success_count += 1
                rtts.append(rtt)

            # Log ICMP packet
            icmp_log = {
                "sequence": seq,
                "success": not packet_lost,
                "rtt": rtt if not packet_lost else None,
                "echo_request": {
                    "src_mac": source_interface.mac,
                    "dest_mac": dest_mac,
                    "src_ip": source_interface.ip,
                    "dest_ip": event.destination_ip,
                    "ttl": 64,
                },
            }

            if not packet_lost:
                icmp_log["echo_reply"] = {
                    "src_mac": dest_mac,
                    "dest_mac": source_interface.mac,
                    "src_ip": event.destination_ip,
                    "dest_ip": source_interface.ip,
                    "ttl": 64,
                }

            logs.append(icmp_log)

            # Respect timeout
            if event.timeout > 0:
                time.sleep(
                    min(event.timeout / 1000, 0.1)
                )  # Convert timeout to seconds, cap at 100ms

        # Prepare final results
        result = {
            "event_id": event.id,
            "status": "success" if success_count > 0 else "failed",
            "action": "ping",
            "details": {
                "source": event.source_interface,
                "destination_ip": event.destination_ip,
                "packets_sent": event.count,
                "packets_received": success_count,
                "loss_percentage": ((event.count - success_count) / event.count) * 100,
                "round_trip_time_ms": {
                    "min": min(rtts) if rtts else None,
                    "max": max(rtts) if rtts else None,
                    "avg": sum(rtts) / len(rtts) if rtts else None,
                },
                "icmp_packets": logs,
                "path_taken": self.get_network_path(source_device_id, dest_device_id),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        return result

    def get_network_path(self, source_id: str, dest_id: str) -> List[str]:
        """Determine the network path between source and destination"""
        path = [source_id]
        current_id = source_id

        while current_id != dest_id:
            next_hop = None
            for conn in self.connections:
                if netid_to_id(conn.from_interface) == current_id:
                    next_hop = netid_to_id(conn.to_interface)
                    break
                elif netid_to_id(conn.to_interface) == current_id:
                    next_hop = netid_to_id(conn.from_interface)
                    break

            if not next_hop or next_hop in path:
                return []  # No path found or loop detected

            path.append(next_hop)
            current_id = next_hop

            if len(path) > 100:  # Prevent infinite loops
                return []

        return path

    def create_error_log(self, event_id: str, error_message: str) -> dict:
        """Create an error log entry"""
        return {
            "event_id": event_id,
            "status": "failed",
            "action": "ping",
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
