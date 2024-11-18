from core.utils import *
import time
from typing import List
from models.connection import *
from models.event import *
from models.pc import *
from models.switch import *


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
