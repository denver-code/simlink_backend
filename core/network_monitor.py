from core.utils import *
import time
from typing import List

from models.connection import *
from models.event import *
from models.pc import *
from models.switch import *


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
