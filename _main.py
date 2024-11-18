import json

from pc import PC
from switch import Switch
from connection import Connection
from event import Event

# import from data.json
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


def netid_to_id(netid):
    return netid.split(".")[0]


def get_devices_by_connection_id(connection: Connection):
    return (
        devices[netid_to_id(connection.from_interface)],
        devices[netid_to_id(connection.to_interface)],
    )


def validate_connection(connection: Connection):
    from_device, to_device = get_devices_by_connection_id(connection)
    return from_device.name != to_device.name


validated_connections = []

for connection in connections:
    if validate_connection(connection):
        validated_connections.append(connection)


# import from events.json
events = []

with open("events.json") as f:
    data = f.read()

data = json.loads(data)
_events = data["events"]

for event in _events:
    events.append(Event(**event))

print(events)
