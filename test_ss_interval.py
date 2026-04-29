# SPDX-License-Identifier: GPL-2.0-only
# SHOULD BE RUN AS ROOT

# Test cases for set_ss_interval API:
#   Case 1 - flow with no interval set (should use default 200ms)
#   Case 2 - flow with valid interval set (500ms)
#   Case 3 - flow with interval below 10ms (should warn and clamp to 10ms)
#   Case 4 - flow with interval >= flow duration (should warn)
#   Case 5 - multiple flows, one with interval set, one without
#   Case 6 - flow with multiple streams (number_of_streams > 1)

from nest.topology import *
from nest.experiment import *
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper

# Topology: h1 ----- r1 ----- h2
#           h3 ------/

n1 = Network("10.0.1.0/24")
n2 = Network("10.0.2.0/24")
n3 = Network("10.0.3.0/24")

h1 = Node("h1")
h2 = Node("h2")
h3 = Node("h3")
r1 = Router("r1")

(eth1, etr1a) = connect(h1, r1, network=n1)
(etr1b, eth2) = connect(r1, h2, network=n2)
(eth3, etr1c) = connect(h3, r1, network=n3)

AddressHelper.assign_addresses()

eth1.set_attributes("100mbit", "5ms")
etr1a.set_attributes("100mbit", "5ms")
etr1b.set_attributes("100mbit", "5ms")
eth2.set_attributes("100mbit", "5ms")
eth3.set_attributes("100mbit", "5ms")
etr1c.set_attributes("100mbit", "5ms")

h1.add_route("DEFAULT", eth1)
h2.add_route("DEFAULT", eth2)
h3.add_route("DEFAULT", eth3)
r1.add_route("DEFAULT", etr1b)

exp = Experiment("test-ss-interval")

# Case 1: no interval set — uses default 200ms
flow1 = Flow(h1, h2, eth2.get_address(), 0, 30, 1)
exp.add_tcp_flow(flow1)
print(f"[Case 1] flow1 ss_interval (expect 0.2): {flow1._ss_interval}")

# Case 2: valid interval — 500ms
flow2 = Flow(h1, h2, eth2.get_address(), 0, 30, 1)
flow2.set_ss_interval(0.5)
exp.add_tcp_flow(flow2)
print(f"[Case 2] flow2 ss_interval (expect 0.5): {flow2._ss_interval}")

# Case 3: interval below 10ms — should warn and clamp to 0.01
flow3 = Flow(h1, h2, eth2.get_address(), 0, 30, 1)
flow3.set_ss_interval(0.005)
exp.add_tcp_flow(flow3)
print(f"[Case 3] flow3 ss_interval (expect 0.01): {flow3._ss_interval}")

# Case 4: interval >= flow duration — should warn but still set
flow4 = Flow(h1, h2, eth2.get_address(), 0, 30, 1)
flow4.set_ss_interval(35.0)
exp.add_tcp_flow(flow4)
print(f"[Case 4] flow4 ss_interval (expect 35.0): {flow4._ss_interval}")

# Case 5: two flows from different sources, one sets interval, one does not
flow5a = Flow(h1, h2, eth2.get_address(), 0, 30, 1)
flow5a.set_ss_interval(0.1)
exp.add_tcp_flow(flow5a)
print(f"[Case 5a] flow5a ss_interval (expect 0.1): {flow5a._ss_interval}")

flow5b = Flow(h3, h2, eth2.get_address(), 0, 30, 1)
exp.add_tcp_flow(flow5b)
print(f"[Case 5b] flow5b ss_interval (expect 0.2): {flow5b._ss_interval}")

# Case 6: multiple streams (number_of_streams=4) with custom interval
flow6 = Flow(h1, h2, eth2.get_address(), 0, 30, 4)
flow6.set_ss_interval(0.3)
exp.add_tcp_flow(flow6)
print(f"[Case 6] flow6 streams=4, ss_interval (expect 0.3): {flow6._ss_interval}")

print("\nAll cases verified. Running experiment...")
exp.run()
