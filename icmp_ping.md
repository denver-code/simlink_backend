```log
Monitoring from PC1's perspective:

=== Traffic captured on pc1 ===
Interface: eth0
Capturing packets relevant to ping from pc1.eth0 to 192.168.1.101

pc1 observed ARP traffic:
[0.514062s] Sent ARP Request
  Who has 192.168.1.101? Tell pc1
[0.531596s] Received ARP Reply
  192.168.1.101 is at 00:1A:2B:3C:4D:5E

ICMP Echo Request (seq=0)
[1.551986s] Incoming ICMP Echo Request
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.100 -> 192.168.1.101
  TTL: 64

ICMP Echo Reply (seq=0)
[1.567817s] Incoming ICMP Echo Reply
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.101 -> 192.168.1.100
  TTL: 64
  Round Trip Time: 0.980ms

ICMP Echo Request (seq=1)
[2.096547s] Incoming ICMP Echo Request
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.100 -> 192.168.1.101
  TTL: 64

ICMP Echo Reply (seq=1)
[2.112179s] Incoming ICMP Echo Reply
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.101 -> 192.168.1.100
  TTL: 64
  Round Trip Time: 1.466ms

ICMP Echo Request (seq=2)
[2.641364s] Incoming ICMP Echo Request
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.100 -> 192.168.1.101
  TTL: 64

ICMP Echo Reply (seq=2)
[2.657339s] Incoming ICMP Echo Reply
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.101 -> 192.168.1.100
  TTL: 64
  Round Trip Time: 0.518ms

ICMP Echo Request (seq=3)
[3.183500s] Incoming ICMP Echo Request
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.100 -> 192.168.1.101
  TTL: 64

ICMP Echo Reply (seq=3)
[3.206353s] Incoming ICMP Echo Reply
  Layer 2: 00:1A:2B:3C:4D:5E -> 00:1A:2B:3C:4D:5E
  Layer 3: 192.168.1.101 -> 192.168.1.100
  TTL: 64
  Round Trip Time: 0.682ms

```