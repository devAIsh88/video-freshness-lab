"""Small named workloads with identical producer schedules for comparisons."""

from .simulation import Config

SCENARIOS = {
    "balanced": Config(freshness_threshold_ms=80),
    "overload": Config(consumer_duration_ms=25, freshness_threshold_ms=80),
    "slowdown-fifo": Config(consumer_duration_ms=40, freshness_threshold_ms=80),
    "slowdown-latest": Config(
        consumer_duration_ms=40, policy="latest", freshness_threshold_ms=80
    ),
}
