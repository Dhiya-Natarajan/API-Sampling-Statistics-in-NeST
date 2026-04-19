# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2026 NITK Surathkal

"""Per-stat-type sampling interval configuration for flows"""

DEFAULT_SAMPLING_INTERVAL = 0.2


class StatsConfig:
    """
    Configures the sampling interval for each statistic type collected during
    an experiment. Different stat collectors (ss, ping) can sample at different
    rates for the same flow, enabling fine-grained control over data resolution
    vs. overhead trade-offs.

    To configure tc (qdisc) sampling interval, pass ``interval`` to
    ``Experiment.require_qdisc_stats()``.

    Attributes
    ----------
    ss : float
        Sampling interval in seconds for socket statistics (default 0.2).
    ping : float
        Sampling interval in seconds for ping/latency statistics (default 0.2).

    Example
    -------
    ::

        flow = Flow(src, dst, dst_addr, 0, 10, 1)
        flow.stats_config = StatsConfig(ss=0.1, ping=0.5)
    """

    DEFAULT_INTERVAL = DEFAULT_SAMPLING_INTERVAL

    def __init__(
        self,
        ss: float = DEFAULT_SAMPLING_INTERVAL,
        ping: float = DEFAULT_SAMPLING_INTERVAL,
    ):
        """
        Parameters
        ----------
        ss : float
            Sampling interval in seconds for socket stats collector (ss).
        ping : float
            Sampling interval in seconds for latency collector (ping).
        """
        self.ss = ss
        self.ping = ping

    def __repr__(self):
        return f"StatsConfig(ss={self.ss!r}, ping={self.ping!r})"
