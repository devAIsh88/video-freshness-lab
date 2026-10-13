"""Fault scripts for the same numbered-item engine; no RTSP protocol claims."""

from dataclasses import replace

from .model import Control
from .simulation import Config

RECOVERY = Config(
    consumer_duration_ms=40,
    freshness_threshold_ms=80,
    no_progress_timeout_ms=25,
    controls=(Control(25, "disconnect"), Control(55, "reconnect")),
)

RECOVERY_SCENARIOS = {
    "normal": Config(freshness_threshold_ms=80, no_progress_timeout_ms=25),
    "consumer-slowdown": Config(
        freshness_threshold_ms=80,
        no_progress_timeout_ms=25,
        controls=(Control(20, "slowdown", 40),),
    ),
    "freeze": Config(
        consumer_duration_ms=40,
        freshness_threshold_ms=80,
        no_progress_timeout_ms=25,
        controls=(Control(20, "freeze"), Control(60, "unfreeze")),
    ),
    "disconnect": replace(RECOVERY, controls=(Control(25, "disconnect"),)),
    "reconnect": RECOVERY,
    "repeated-recovery": replace(
        RECOVERY,
        duration_ms=150,
        controls=(
            Control(25, "disconnect"),
            Control(55, "reconnect"),
            Control(85, "disconnect"),
            Control(115, "reconnect"),
        ),
    ),
    "no-progress": Config(
        freshness_threshold_ms=80,
        no_progress_timeout_ms=25,
        controls=(Control(10, "freeze"), Control(90, "unfreeze")),
    ),
    "obsolete-delivery": replace(
        RECOVERY,
        duration_ms=60,
        controls=(Control(10, "disconnect"), Control(20, "reconnect")),
    ),
    "session-filter": replace(RECOVERY, session_filter=True),
}
