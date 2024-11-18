# class MockProtocol:

#     def __init__(self, network, peer):
#         self.network = network
#         self.peer = peer

#     async def rpc(self, address, name, *args):
#         peer = self.network.peers[address[0]]
#         proc = getattr(peer, name)
#         start = time()
#         out = await proc((self.peer._uid, None), *args)
#         delta = time() - start
#         assert delta < 5, "RPCProtocol allows 5s delay only"
#         return out


# class MockNetwork:

#     def __init__(self):
#         self.peers = dict()

#     def add(self, peer):
#         peer._protocol = MockProtocol(self, peer)
#         self.peers[peer._uid] = peer

#     def choice(self):
#         return random.choice(list(self.peers.values()))


# async def simple_network():
#     network = MockNetwork()
#     for i in range(5):
#         peer = make_peer()
#         network.add(peer)
#     bootstrap = peer
#     for peer in network.peers.values():
#         await peer.bootstrap((bootstrap._uid, None))
#     for peer in network.peers.values():
#         await peer.bootstrap((bootstrap._uid, None))

#     # run connect, this simulate the peers connecting to an existing
#     # network.
#     for peer in network.peers.values():
#         await peer.connect()

#     return network


# @pytest.mark.asyncio
# async def test_dict(make_network):
#     network = await make_network()
#     # setup
#     value = b"test value"
#     key = peer.hash(value)
#     # make network and peers
#     one = network.choice()
#     two = network.choice()
#     three = network.choice()
#     four = network.choice()

#     # exec
#     out = await three.set(value)

#     # check
#     assert out == key

#     fallback = list()
#     for xxx in (one, two, three, four):
#         try:
#             out = await xxx.get(key)
#         except KeyError:
#             fallback.append(xxx)
#         else:
#             assert out == value

#     for xxx in fallback:
#         log.warning("fallback for peer %r", xxx)
#         out = await xxx.get_at(key, three._uid)
#         assert out == value
import time
from collections import defaultdict


class Switch:
    def __init__(self):
        # ARP table maps IP addresses to MAC addresses
        self.arp_table = {}
        # Switch ports (for simulation purposes, we assume only two ports connected to PCs)
        self.ports = {1: None, 2: None}  # Example ports connected to two PCs
        self.packet_buffer = defaultdict(list)  # Buffer for incoming packets

    def handle_arp_request(self, src_ip, dst_ip, src_mac):
        """
        Simulates the handling of an ARP request.
        """
        print(f"ARP request from {src_ip} ({src_mac}) asking for {dst_ip}")

        if dst_ip in self.arp_table:
            # If we have the MAC address, send ARP reply
            dst_mac = self.arp_table[dst_ip]
            print(f"Found MAC for {dst_ip}: {dst_mac}. Sending ARP reply.")
            self.send_arp_reply(src_ip, dst_ip, dst_mac, src_mac)
        else:
            # If not found, buffer the request and wait for a response
            print(f"MAC for {dst_ip} not found. Request buffered.")
            self.packet_buffer[dst_ip].append((src_ip, src_mac))

    def handle_arp_reply(self, src_ip, dst_ip, src_mac, dst_mac):
        """
        Simulates handling of an ARP reply. It updates the ARP table.
        """
        print(f"ARP reply received: {src_ip} ({src_mac}) -> {dst_ip} ({dst_mac})")
        self.arp_table[src_ip] = src_mac
        self.arp_table[dst_ip] = dst_mac

        # Once the MAC address is learned, forward any buffered packets
        if dst_ip in self.packet_buffer:
            for src_ip, src_mac in self.packet_buffer[dst_ip]:
                print(f"Forwarding buffered packets for {dst_ip} from {src_ip}")
                self.forward_packet(src_ip, dst_ip, src_mac, dst_mac)

    def send_arp_reply(self, src_ip, dst_ip, src_mac, dst_mac):
        """
        Simulates sending an ARP reply from the destination to the source.
        """
        print(f"Sending ARP reply: {src_ip} ({src_mac}) -> {dst_ip} ({dst_mac})")
        # ARP reply is a unicast message
        self.handle_arp_reply(src_ip, dst_ip, src_mac, dst_mac)

    def forward_packet(self, src_ip, dst_ip, src_mac, dst_mac):
        """
        Simulates forwarding a packet between PCs connected to the switch.
        """
        print(f"Forwarding packet from {src_ip} ({src_mac}) to {dst_ip} ({dst_mac})")

        # Check which port the destination MAC address is associated with and forward the packet
        for port, device_mac in self.ports.items():
            if device_mac == dst_mac:
                print(f"Packet forwarded to port {port}")
                break
        else:
            print("Destination MAC address not found in ports. Packet dropped.")

    def connect_device(self, port, mac_address):
        """
        Connect a device (PC) to a port on the switch, associating the MAC address.
        """
        if port in self.ports:
            self.ports[port] = mac_address
            print(f"Device connected to port {port} with MAC address {mac_address}")
        else:
            print("Invalid port")


# Example usage:

# Create a switch instance
switch = Switch()

# Connect two devices with MAC addresses
switch.connect_device(1, "00:11:22:33:44:55")  # PC 1
switch.connect_device(2, "66:77:88:99:AA:BB")  # PC 2

# PC 1 sends an ARP request for PC 2's MAC address
switch.handle_arp_request("192.168.0.1", "192.168.0.2", "00:11:22:33:44:55")

# PC 2 replies with an ARP response
switch.handle_arp_reply(
    "192.168.0.2", "192.168.0.1", "66:77:88:99:AA:BB", "00:11:22:33:44:55"
)

# Now PC 1 can forward a packet to PC 2
switch.forward_packet(
    "192.168.0.1", "192.168.0.2", "00:11:22:33:44:55", "66:77:88:99:AA:BB"
)
