from dataclasses import dataclass
from datetime import datetime
import json
import random
import ipaddress
import time
from typing import Dict, List, Optional, Tuple

from connection import *
from event import *
from pc import *
from switch import *


def netid_to_id(netid):
    return netid.split(".")[0]


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


def simulate_network_events(
    devices: Dict, connections: List[Connection], events: List[Event]
) -> Dict:
    """Run network simulation for all events"""
    simulator = NetworkSimulator(devices, connections)
    results = []

    for event in events:
        if event.type == "ping":
            result = simulator.simulate_ping(event)
            results.append(result)

    return {"logs": results}


devices = {}
connections = []

with open("data.json") as f:
    data = f.read()

data = json.loads(data)
_devices = data["nodes"]
_connections = data["connections"]

for device in _devices:
    if device["type"] == "PC":
        devices[device["id"]] = PC(**device)
    elif device["type"] == "Switch":
        devices[device["id"]] = Switch(**device)

for connection in _connections:
    connections.append(Connection(**connection))

events = []

with open("events.json") as f:
    data = f.read()

data = json.loads(data)
_events = data["events"]

for event in _events:
    events.append(Event(**event))


class NetworkMonitor:
    def __init__(self):
        self.start_time = time.time()
        # Network characteristics
        self.switch_latency = 0.0002  # 0.2ms switch latency
        self.propagation_delay = 0.0005  # 0.5ms cable propagation delay
        self.processing_delay = 0.001  # 1ms host processing delay

    def simulate_delay(self, source_device: str, dest_device: str, path: List[str]):
        """Simulate realistic network delays based on path"""
        # Processing delay at source
        time.sleep(self.processing_delay)

        # Network traversal delay
        for i in range(len(path) - 1):
            # Switch processing delay
            if "switch" in path[i] or "switch" in path[i + 1]:
                time.sleep(self.switch_latency)
            # Cable propagation delay
            time.sleep(self.propagation_delay)

        # Processing delay at destination
        time.sleep(self.processing_delay)

    def print_packet(self, packet_data: dict, direction: str = "->", indent: int = 0):
        timestamp = time.time() - self.start_time
        indent_str = "  " * indent
        print(
            f"{indent_str}[{timestamp:.3f}s] {packet_data['src_mac']} {direction} {packet_data['dest_mac']}"
        )
        print(
            f"{indent_str}     {packet_data['src_ip']} {direction} {packet_data['dest_ip']}"
        )
        # Add slight delay for packet printing to simulate real-time monitoring
        time.sleep(0.05)

    def print_arp(self, arp_data: dict, path: List[str]):
        timestamp = time.time() - self.start_time
        print(f"\n[{timestamp:.3f}s] ARP Resolution Started:")
        print(
            f"  {arp_data['source_ip']} ({arp_data['source_mac']}) -> Who has {arp_data['target_ip']}?"
        )

        # Simulate ARP request propagation
        self.simulate_delay(arp_data["source_ip"], arp_data["target_ip"], path)

        timestamp = time.time() - self.start_time
        print(f"[{timestamp:.3f}s] ARP Request Broadcast:")
        print(f"  Broadcasting on all switch ports...")

        # Simulate processing time on target host
        time.sleep(self.processing_delay * 2)

        timestamp = time.time() - self.start_time
        print(f"[{timestamp:.3f}s] ARP Reply:")
        print(
            f"  {arp_data['target_ip']} -> {arp_data['source_ip']}: I'm at {arp_data['target_mac']}"
        )

        # Simulate ARP reply propagation
        self.simulate_delay(arp_data["target_ip"], arp_data["source_ip"], path)

    def monitor_ping(self, ping_result: dict):
        event_details = ping_result["details"]
        print(
            f"\n=== Starting Ping from {event_details['source']} to {event_details['destination_ip']} ==="
        )
        print(f"Sending {event_details['packets_sent']} packets...")
        time.sleep(0.5)  # Initial setup delay

        # Print network path
        path = event_details.get("path_taken", [])
        if path:
            print("\nNetwork path:")
            for i, node in enumerate(path):
                if i < len(path) - 1:
                    print(f"  {node} -> {path[i+1]}")
                    time.sleep(0.1)  # Delay between printing each hop
            print()

        # First, simulate ARP if needed (first ping only)
        print("Performing ARP resolution...")
        self.print_arp(
            {
                "source_ip": event_details["source"].split(".")[0],
                "source_mac": event_details["icmp_packets"][0]["echo_request"][
                    "src_mac"
                ],
                "target_ip": event_details["destination_ip"],
                "target_mac": event_details["icmp_packets"][0]["echo_request"][
                    "dest_mac"
                ],
            },
            path,
        )
        print("\nARP resolution completed. Starting ping sequence...")
        time.sleep(0.5)

        # Process each ICMP packet
        for packet in event_details["icmp_packets"]:
            seq_num = packet["sequence"]

            # Add delay between ping sequences
            if seq_num > 0:
                time.sleep(1.0)  # 1 second between pings

            print(f"\nSequence {seq_num + 1}:")
            # Print Echo Request
            self.print_packet(packet["echo_request"], "->", 1)

            if packet["success"]:
                # Simulate network traversal for request
                self.simulate_delay(
                    packet["echo_request"]["src_ip"],
                    packet["echo_request"]["dest_ip"],
                    path,
                )

                # Print Echo Reply
                self.print_packet(packet["echo_reply"], "<-", 1)

                # Simulate network traversal for reply
                self.simulate_delay(
                    packet["echo_reply"]["src_ip"],
                    packet["echo_reply"]["dest_ip"],
                    path,
                )

                print(f"  RTT: {packet['rtt']:.3f}ms")
            else:
                # Simulate timeout
                time.sleep(2.0)
                print("  * Request timed out *")

        # Print summary with delay
        time.sleep(0.5)
        print(f"\n=== Ping Statistics ===")
        time.sleep(0.2)
        print(
            f"Packets: Sent = {event_details['packets_sent']}, "
            f"Received = {event_details['packets_received']}, "
            f"Lost = {event_details['packets_sent'] - event_details['packets_received']} "
            f"({event_details['loss_percentage']:.1f}% loss)"
        )

        if event_details["packets_received"] > 0:
            time.sleep(0.2)
            rtt = event_details["round_trip_time_ms"]
            print(f"Round-trip time (ms):")
            time.sleep(0.1)
            print(f"    Minimum = {rtt['min']:.3f}ms")
            time.sleep(0.1)
            print(f"    Maximum = {rtt['max']:.3f}ms")
            time.sleep(0.1)
            print(f"    Average = {rtt['avg']:.3f}ms")


def run_realtime_simulation(simulation_results: dict):
    monitor = NetworkMonitor()

    for log_entry in simulation_results["logs"]:
        if log_entry["status"] == "failed":
            print(f"\n❌ Error: {log_entry['error']}")
            continue

        monitor.monitor_ping(log_entry)
        # Add delay between different ping commands if multiple events
        time.sleep(1.0)


class DevicePerspectiveMonitor:
    def __init__(self, monitor_device_id: str, monitor_interface: str = None):
        self.start_time = time.time()
        self.monitor_device_id = monitor_device_id
        self.monitor_interface = monitor_interface
        self.switch_latency = 0.0002
        self.propagation_delay = 0.0005
        self.processing_delay = 0.001

    def is_packet_visible(self, packet_data: dict, path: List[str]) -> bool:
        """Determine if packet is visible from monitoring device's perspective"""
        # Extract device IDs from full interface names or IPs
        src_device = packet_data["src_ip"].split(".")[0]
        dest_device = packet_data["dest_ip"].split(".")[0]

        # Debug print
        print(
            f"Debug - Checking visibility: src={src_device}, dest={dest_device}, monitor={self.monitor_device_id}"
        )

        # If monitoring a switch, we see all packets that traverse it
        if "switch" in self.monitor_device_id:
            return self.monitor_device_id in path

        # If monitoring an end device, we see packets to/from it
        return (
            self.monitor_device_id == src_device
            or self.monitor_device_id == dest_device
        )

    def format_packet(self, packet_data: dict, packet_type: str) -> str:
        """Format packet information based on type and perspective"""
        timestamp = time.time() - self.start_time

        # Determine packet direction
        is_source = packet_data["src_ip"].startswith(self.monitor_device_id)
        direction = "Outgoing" if is_source else "Incoming"
        if "switch" in self.monitor_device_id:
            direction = "Forward"

        return (
            f"[{timestamp:.6f}s] {direction} {packet_type}\n"
            f"  Layer 2: {packet_data['src_mac']} -> {packet_data['dest_mac']}\n"
            f"  Layer 3: {packet_data['src_ip']} -> {packet_data['dest_ip']}"
        )

    def monitor_ping_from_perspective(self, ping_result: dict):
        event_details = ping_result["details"]
        path = event_details.get("path_taken", [])

        # Print initial monitoring information
        print(f"\n=== Traffic captured on {self.monitor_device_id} ===")
        if self.monitor_interface:
            print(f"Interface: {self.monitor_interface}")
        print(
            f"Capturing packets relevant to ping from {event_details['source']} to {event_details['destination_ip']}"
        )
        time.sleep(0.5)

        # Show ARP resolution
        self.print_arp_from_perspective(
            {
                "source_ip": event_details["source"].split(".")[0],
                "source_mac": event_details["icmp_packets"][0]["echo_request"][
                    "src_mac"
                ],
                "target_ip": event_details["destination_ip"],
                "target_mac": event_details["icmp_packets"][0]["echo_request"][
                    "dest_mac"
                ],
            },
            path,
        )
        time.sleep(0.5)

        # Process ICMP packets
        for packet in event_details["icmp_packets"]:
            seq_num = packet["sequence"]
            time.sleep(0.5)  # Delay between packets

            # Echo Request
            echo_req = packet["echo_request"]
            print(f"\nICMP Echo Request (seq={seq_num})")
            print(self.format_packet(echo_req, "ICMP Echo Request"))
            print(f"  TTL: {echo_req.get('ttl', 64)}")
            self.simulate_delay(path)

            # Echo Reply (if successful)
            if packet["success"]:
                echo_reply = packet["echo_reply"]
                print(f"\nICMP Echo Reply (seq={seq_num})")
                print(self.format_packet(echo_reply, "ICMP Echo Reply"))
                print(f"  TTL: {echo_reply.get('ttl', 64)}")

                # Show RTT only for the monitoring device if it's the source
                if self.monitor_device_id == event_details["source"].split(".")[0]:
                    print(f"  Round Trip Time: {packet['rtt']:.3f}ms")

                self.simulate_delay(path)

    def print_arp_from_perspective(self, arp_data: dict, path: List[str]):
        timestamp = time.time() - self.start_time

        print(f"\n{self.monitor_device_id} observed ARP traffic:")

        if self.monitor_device_id == arp_data["source_ip"]:
            print(f"[{timestamp:.6f}s] Sent ARP Request")
            print(f"  Who has {arp_data['target_ip']}? Tell {arp_data['source_ip']}")

        self.simulate_delay(path)
        timestamp = time.time() - self.start_time

        if self.monitor_device_id == arp_data["source_ip"]:
            print(f"[{timestamp:.6f}s] Received ARP Reply")
            print(f"  {arp_data['target_ip']} is at {arp_data['target_mac']}")

    def simulate_delay(self, path: List[str]):
        """Simulate network delays based on path"""
        for i in range(len(path) - 1):
            if "switch" in path[i] or "switch" in path[i + 1]:
                time.sleep(self.switch_latency)
            time.sleep(self.propagation_delay)
        time.sleep(self.processing_delay)


def monitor_from_device_perspective(
    simulation_results: dict, device_id: str, interface: str = None
):
    monitor = DevicePerspectiveMonitor(device_id, interface)

    for log_entry in simulation_results["logs"]:
        if log_entry["status"] == "failed":
            if device_id in log_entry.get("source", ""):
                print(f"\n❌ Error on {device_id}: {log_entry['error']}")
            continue

        monitor.monitor_ping_from_perspective(log_entry)
        time.sleep(1.0)


# Example usage:
simulation_results = simulate_network_events(devices, connections, events)

# Monitor from PC1's perspective
print("\nMonitoring from PC1's perspective:")
monitor_from_device_perspective(simulation_results, "pc1", "eth0")

# if __name__ == "__main__":
#     results = simulate_network_events(devices, connections, events)

#     # Print or process results
#     # print(json.dumps(results, indent=2))

#     run_realtime_simulation(results)
