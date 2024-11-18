import json
import time
from typing import Dict, List

from core.device_monitor import DevicePerspectiveMonitor
from core.network_monitor import NetworkMonitor
from core.simulator import NetworkSimulator
from models.event import *
from models.pc import *
from models.switch import *
from models.connection import *


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


def run_realtime_simulation(simulation_results: dict):
    monitor = NetworkMonitor()

    for log_entry in simulation_results["logs"]:
        if log_entry["status"] == "failed":
            print(f"\n❌ Error: {log_entry['error']}")
            continue

        monitor.monitor_ping(log_entry)
        # Add delay between different ping commands if multiple events
        time.sleep(1.0)


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


def parse_data(data_file, events_file):
    devices = {}
    connections = []
    events = []

    with open(data_file) as f:
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

    with open(events_file) as f:
        data = f.read()

    data = json.loads(data)
    _events = data["events"]

    for event in _events:
        events.append(Event(**event))

    return devices, connections, events


devices, connections, events = parse_data("data.json", "events.json")
simulation_results = simulate_network_events(devices, connections, events)

# Monitor from PC1's perspective
print("\nMonitoring from PC1's perspective:")
monitor_from_device_perspective(simulation_results, "pc1", "eth0")
