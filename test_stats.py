########################
# sudo python3 test_stats.py
########################

from nest.topology import Node, connect
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper
from nest.experiment import Experiment, Flow, StatsConfig

print("\n[SS ONLY TEST] ss interval = 0.5 over 10 seconds")

# Create topology
n1 = Node("n1")
n2 = Node("n2")

(i1, i2) = connect(n1, n2, network=Network("10.0.0.0/24"))
AddressHelper.assign_addresses()

# Experiment
exp = Experiment("ss-only-test")
exp.return_results = True

flow = Flow(n1, n2, i2.get_address(), 0, 10, 1)
flow.stats_config = StatsConfig(ss=0.5)   # only ss changed

exp.add_tcp_flow(flow)

# Run
results = exp.run()

# -----------------------------
# Extract ss samples
# -----------------------------
ss_results = results.get("ss", {})
ss_samples = []

for ns_data in ss_results.values():
    if isinstance(ns_data, list):
        for item in ns_data:
            if isinstance(item, dict):
                for dst_data in item.values():
                    for port_data in dst_data.values():
                        if isinstance(port_data, list):
                            ss_samples.extend(
                                e for e in port_data
                                if isinstance(e, dict) and "timestamp" in e
                            )

# -----------------------------
# Result check
# -----------------------------
expected = int(10 / 0.5)

print(f"\nExpected ~{expected} samples")
print(f"Got {len(ss_samples)} samples")

if abs(len(ss_samples) - expected) <= 5:
    print("PASS ✅ ss interval working")
else:
    print("FAIL ❌ ss interval not working")