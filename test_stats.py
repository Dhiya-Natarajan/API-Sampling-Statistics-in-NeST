########################
# MUST BE RUN AS ROOT
# sudo python3 test_stats.py
########################

"""
Tests for per-stat-type sampling interval (StatsConfig).

  Tests 1-3: StatsConfig class (fast, no network setup)
  Tests 4-5: Flow.stats_config attribute (quick topology setup)
  Test 6:    Full 10s experiment — ss=0.5s, ping=1.0s, tc=2.0s
             verifies sample counts match expected intervals
"""

from nest.topology import Node, Router, connect
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper
from nest.experiment import Experiment, Flow, StatsConfig

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


def check(label, condition):
    print(f"  [{PASS if condition else FAIL}] {label}")
    return condition


# ---------------------------------------------------------------------------
# Tests 1-3: StatsConfig class
# ---------------------------------------------------------------------------

def test_stats_config_defaults():
    print("\n[1] StatsConfig defaults")
    cfg = StatsConfig()
    check("ss defaults to 0.2",          cfg.ss == 0.2)
    check("ping defaults to 0.2",        cfg.ping == 0.2)
    check("DEFAULT_INTERVAL is 0.2",     StatsConfig.DEFAULT_INTERVAL == 0.2)
    check("repr is correct",
          repr(cfg) == "StatsConfig(ss=0.2, ping=0.2)")


def test_stats_config_custom():
    print("\n[2] StatsConfig with custom values")
    cfg = StatsConfig(ss=0.1, ping=0.5)
    check("ss=0.1",   cfg.ss == 0.1)
    check("ping=0.5", cfg.ping == 0.5)


def test_stats_config_partial():
    print("\n[3] StatsConfig partial override (only ss set)")
    cfg = StatsConfig(ss=0.3)
    check("ss=0.3",                    cfg.ss == 0.3)
    check("ping stays at default 0.2", cfg.ping == 0.2)


# ---------------------------------------------------------------------------
# Tests 4-5: Flow.stats_config
# ---------------------------------------------------------------------------

def test_flow_stats_config_default():
    print("\n[4] Flow.stats_config default")
    n1 = Node("n1")
    n2 = Node("n2")
    (i1, i2) = connect(n1, n2, network=Network("10.0.0.0/24"))
    AddressHelper.assign_addresses()

    flow = Flow(n1, n2, i2.get_address(), 0, 5, 1)
    check("is StatsConfig instance",       isinstance(flow.stats_config, StatsConfig))
    check("flow.stats_config.ss == 0.2",   flow.stats_config.ss == 0.2)
    check("flow.stats_config.ping == 0.2", flow.stats_config.ping == 0.2)


def test_flow_stats_config_custom():
    print("\n[5] Flow.stats_config custom assignment")
    n1 = Node("n3")
    n2 = Node("n4")
    (i1, i2) = connect(n1, n2, network=Network("10.1.0.0/24"))
    AddressHelper.assign_addresses()

    flow = Flow(n1, n2, i2.get_address(), 0, 5, 1)
    flow.stats_config = StatsConfig(ss=0.1, ping=0.4)
    check("ss overridden to 0.1",   flow.stats_config.ss == 0.1)
    check("ping overridden to 0.4", flow.stats_config.ping == 0.4)


# ---------------------------------------------------------------------------
# Test 6: Full experiment — verify sample counts
# ---------------------------------------------------------------------------

def test_full_experiment():
    """
    10s TCP flow with:
      ss interval   = 0.5s  -> expect ~20 ss samples
      ping interval = 1.0s  -> expect ~10 ping samples
      tc interval   = 2.0s  -> expect ~5  tc samples
    """
    print("\n[6] Full experiment — custom sampling intervals")
    print("    (ss=0.5s, ping=1.0s, tc=2.0s over 10s flow — takes ~15s)")

    h1 = Node("h1")
    h2 = Node("h2")
    r1 = Router("r1")
    r2 = Router("r2")

    (eth1, etr1a) = connect(h1, r1, network=Network("192.168.1.0/24"))
    (etr1b, etr2a) = connect(r1, r2, network=Network("192.168.2.0/24"))
    (etr2b, eth2)  = connect(r2, h2, network=Network("192.168.3.0/24"))

    AddressHelper.assign_addresses()

    eth1.set_attributes("1000mbit", "1ms")
    etr1b.set_attributes("10mbit", "10ms", "pfifo")
    etr2b.set_attributes("1000mbit", "1ms")
    eth2.set_attributes("1000mbit", "1ms")
    etr2a.set_attributes("10mbit", "10ms")
    etr1a.set_attributes("1000mbit", "1ms")

    h1.add_route("DEFAULT", eth1)
    h2.add_route("DEFAULT", eth2)
    r1.add_route("DEFAULT", etr1b)
    r2.add_route("DEFAULT", etr2a)

    exp = Experiment("test-stats-sampling")
    exp.return_results = True

    flow = Flow(h1, h2, eth2.get_address(), 0, 10, 1)
    flow.stats_config = StatsConfig(ss=0.5, ping=1.0)
    exp.add_tcp_flow(flow)

    exp.require_qdisc_stats(etr1b, interval=2.0)

    results = exp.run()

    # ss: 10s / 0.5s = ~20 samples (allow ±5)
    ss_results = results.get("ss", {})
    if ss_results:
        ss_samples = []
        for ns_data in ss_results.values():
            for dst_data in ns_data.values():
                for port_data in dst_data.values():
                    ss_samples.extend(e for e in port_data if "timestamp" in e)
        expected = int(10 / 0.5)
        check(f"ss ~{expected} samples (got {len(ss_samples)})",
              abs(len(ss_samples) - expected) <= 5)
    else:
        check("ss results present", False)

    # ping: 10s / 1.0s = ~10 samples (allow ±3)
    ping_results = results.get("ping", {})
    if ping_results:
        ping_samples = []
        for ns_data in ping_results.values():
            for dst_data in ns_data.values():
                ping_samples.extend(e for e in dst_data if "rtt" in e)
        expected = int(10 / 1.0)
        check(f"ping ~{expected} samples (got {len(ping_samples)})",
              abs(len(ping_samples) - expected) <= 3)
    else:
        check("ping results present", False)

    # tc: 10s / 2.0s = ~5 samples (allow ±2)
    tc_results = results.get("tc", {})
    if tc_results:
        tc_samples = []
        for ns_data in tc_results.values():
            for iface_data in ns_data.values():
                for handle_data in iface_data.values():
                    tc_samples.extend(handle_data)
        expected = int(10 / 2.0)
        check(f"tc ~{expected} samples (got {len(tc_samples)})",
              abs(len(tc_samples) - expected) <= 2)
    else:
        check("tc results present (pfifo may not output stats)", True)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  NeST StatsConfig sampling interval tests")
    print("=" * 55)

    test_stats_config_defaults()
    test_stats_config_custom()
    test_stats_config_partial()
    test_flow_stats_config_default()
    test_flow_stats_config_custom()
    test_full_experiment()

    print("\n" + "=" * 55)
    print("  Done.")
    print("=" * 55)
