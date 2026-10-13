import json
import subprocess
import sys
from dataclasses import replace

import pytest

from video_freshness_lab.clock import VirtualClock
from video_freshness_lab.model import Control
from video_freshness_lab.recovery_experiments import RECOVERY, RECOVERY_SCENARIOS
from video_freshness_lab.simulation import Config, Simulator


def test_session_lifecycle_and_provenance_across_reconnect() -> None:
    result = Simulator(RECOVERY).run()
    assert [(f.session_id, f.sequence, f.produced_at_ms) for f in result.frames] == [
        (0, 0, 0),
        (0, 1, 10),
        (0, 2, 20),
        (1, 0, 60),
        (1, 1, 70),
        (1, 2, 80),
        (1, 3, 90),
    ]
    assert [
        (e.session_id, e.at_ms) for e in result.events if e.kind == "session_started"
    ] == [(0, 0), (1, 55)]
    assert [
        (e.session_id, e.at_ms) for e in result.events if e.kind == "session_ended"
    ] == [(0, 25), (1, 280)]
    assert len({f.frame_id for f in result.frames}) == 7
    assert result.metrics.obsolete_session_frames_detected == 3
    assert result.metrics.obsolete_session_outputs == 3
    # Lag remains local to each retired evidence epoch, not the new sequence head.
    assert [p.lag_at_completion for p in result.processing[:3]] == [2, 1, 0]


def test_disconnect_retains_queue_and_processing_in_baseline() -> None:
    result = Simulator(RECOVERY).run()
    old = result.processing[:3]
    assert [p.completed_at_ms for p in old] == [40, 80, 120]
    assert [p.started_at_ms for p in old] == [0, 40, 80]
    assert all(p.emitted and p.obsolete_at_completion for p in old)
    assert (
        next(e for e in result.events if e.kind == "stream_interrupted").queue_depth
        == 2
    )


def test_filter_checks_both_dequeue_and_in_flight_emission() -> None:
    result = Simulator(replace(RECOVERY, session_filter=True)).run()
    assert result.metrics.frames_consumed == 4
    assert result.metrics.frames_processed == 5
    assert result.metrics.frames_rejected == 3
    assert result.metrics.obsolete_session_outputs == 0
    assert [d.frame.sequence for d in result.drops] == [0, 1, 2]
    assert [d.at_ms for d in result.drops] == [40, 40, 40]
    assert all(d.reason == "obsolete_session" for d in result.drops)
    assert result.processing[0].started_at_ms == 0
    assert not result.processing[0].emitted
    assert result.processing[0].completed_at_ms == 40
    assert all(p.frame.session_id == 1 for p in result.processing if p.emitted)
    # Valid-session FIFO output may still exceed the independent age budget.
    assert result.metrics.result_freshness_violations == 2


def test_latest_replacement_does_not_fix_obsolete_active_work() -> None:
    baseline = Simulator(replace(RECOVERY, policy="latest")).run()
    filtered = Simulator(replace(RECOVERY, policy="latest", session_filter=True)).run()
    assert baseline.frames == filtered.frames
    assert baseline.metrics.max_completion_age_ms == 70
    assert baseline.metrics.result_freshness_violations == 0
    assert baseline.metrics.obsolete_session_outputs == 2
    assert filtered.metrics.obsolete_session_outputs == 0
    assert filtered.metrics.frames_rejected == 2
    assert filtered.metrics.frames_replaced == 3
    assert filtered.metrics.frames_consumed == 2
    assert filtered.metrics.frames_dropped == 5
    assert filtered.metrics.max_completion_age_ms == 50


@pytest.mark.parametrize("policy", ["fifo", "latest"])
def test_invalidation_drops_waiting_but_does_not_cancel_active_work(policy) -> None:
    config = replace(RECOVERY, policy=policy, queue_on_disconnect="invalidate")
    result = Simulator(config).run()
    expected = 2 if policy == "fifo" else 1
    assert result.metrics.frames_invalidated == expected
    assert all(d.at_ms == 25 for d in result.drops if d.reason == "invalidated_session")
    assert result.metrics.obsolete_session_outputs == 1
    protected = Simulator(replace(config, session_filter=True)).run()
    assert protected.metrics.obsolete_session_outputs == 0
    assert protected.metrics.frames_rejected == 1


@pytest.mark.parametrize("filtered", [False, True])
def test_boundary_control_precedes_same_time_completion(filtered) -> None:
    config = Config(
        duration_ms=30,
        session_filter=filtered,
        freshness_threshold_ms=10,
        controls=(Control(10, "disconnect"), Control(20, "reconnect")),
    )
    result = Simulator(config).run()
    assert result.metrics.obsolete_session_outputs == (0 if filtered else 1)
    assert result.metrics.frames_rejected == (1 if filtered else 0)
    assert result.metrics.result_freshness_violations == 0
    at_ten = [e.kind for e in result.events if e.at_ms == 10]
    assert at_ten[:3] == [
        "session_ended",
        "stream_interrupted",
        "old_session_frame_detected",
    ]
    assert at_ten[3] == ("frame_dropped" if filtered else "frame_consumed")


def test_repeated_recovery_does_not_reuse_epochs() -> None:
    result = Simulator(RECOVERY_SCENARIOS["repeated-recovery"]).run()
    assert [e.session_id for e in result.events if e.kind == "session_started"] == [
        0,
        1,
        2,
    ]
    assert [
        (e.at_ms, e.reason) for e in result.events if e.kind == "stream_recovered"
    ] == [(55, "reconnect"), (115, "reconnect")]
    assert [(f.session_id, f.sequence) for f in result.frames] == [
        (epoch, sequence) for epoch in range(3) for sequence in range(3)
    ]
    assert result.metrics.obsolete_session_outputs == 6
    assert result.metrics.no_progress_intervals == 2
    filtered = Simulator(replace(result.config, session_filter=True)).run()
    assert filtered.metrics.obsolete_session_outputs == 0


def test_freeze_preserves_session_and_sequence_but_stops_source_progress() -> None:
    result = Simulator(RECOVERY_SCENARIOS["freeze"]).run()
    assert [f.produced_at_ms for f in result.frames] == [0, 10, 60, 70, 80, 90]
    assert [f.sequence for f in result.frames] == list(range(6))
    assert {f.session_id for f in result.frames} == {0}
    gaps = [e for e in result.events if e.kind == "no_progress"]
    assert [(e.since_ms, e.at_ms) for e in gaps] == [(10, 35)]
    assert result.metrics.obsolete_session_outputs == 0
    assert result.metrics.result_freshness_violations == 3


def test_no_progress_alert_once_per_episode_and_resets_on_new_evidence() -> None:
    result = Simulator(
        Config(
            no_progress_timeout_ms=25,
            controls=(
                Control(20, "freeze"),
                Control(40, "unfreeze"),
                Control(60, "freeze"),
                Control(80, "unfreeze"),
            ),
        )
    ).run()
    assert [
        (e.since_ms, e.at_ms) for e in result.events if e.kind == "no_progress"
    ] == [(10, 35), (50, 75)]
    long_freeze = Simulator(RECOVERY_SCENARIOS["no-progress"]).run()
    assert long_freeze.metrics.no_progress_intervals == 1
    assert [f.produced_at_ms for f in long_freeze.frames] == [0, 90]


def test_progress_at_watchdog_deadline_wins_and_horizon_stops_monitor() -> None:
    clock = VirtualClock()
    normal = Simulator(Config(duration_ms=40, no_progress_timeout_ms=10), clock).run()
    assert normal.metrics.no_progress_intervals == 0
    assert clock.pending_count == 0
    stalled = Simulator(
        Config(
            duration_ms=30,
            no_progress_timeout_ms=10,
            controls=(Control(0, "disconnect"),),
        )
    ).run()
    assert stalled.metrics.frames_produced == stalled.metrics.frames_consumed == 0
    assert stalled.metrics.max_completion_age_ms is None
    assert stalled.metrics.no_progress_intervals == 1
    assert stalled.metrics.finished_at_ms == 30


def test_same_timestamp_controls_preserve_declared_order() -> None:
    result = Simulator(
        Config(
            duration_ms=20,
            controls=(
                Control(5, "freeze"),
                Control(5, "disconnect"),
                Control(5, "reconnect"),
            ),
        )
    ).run()
    assert [e.kind for e in result.events if e.at_ms == 5] == [
        "stream_interrupted",
        "session_ended",
        "stream_interrupted",
        "session_started",
        "stream_recovered",
    ]
    assert [(f.session_id, f.produced_at_ms) for f in result.frames] == [
        (0, 0),
        (1, 10),
    ]


def test_consumer_slowdown_does_not_retime_in_progress_work() -> None:
    result = Simulator(
        Config(
            duration_ms=40,
            controls=(Control(5, "slowdown", 40), Control(15, "slowdown", 10)),
        )
    ).run()
    assert [p.completed_at_ms for p in result.processing] == [10, 50, 60, 70]
    assert [p.age_at_completion_ms for p in result.processing] == [10, 40, 40, 40]


@pytest.mark.parametrize(
    "config", RECOVERY_SCENARIOS.values(), ids=RECOVERY_SCENARIOS.keys()
)
@pytest.mark.parametrize("policy", ["fifo", "latest"])
@pytest.mark.parametrize("filtered", [False, True])
@pytest.mark.parametrize("queue_policy", ["retain", "invalidate"])
def test_recovery_conservation_provenance_and_filter_contract(
    config, policy, filtered, queue_policy
) -> None:
    result = Simulator(
        replace(
            config,
            policy=policy,
            session_filter=filtered,
            queue_on_disconnect=queue_policy,
        )
    ).run()
    outputs = {p.frame.frame_id for p in result.processing if p.emitted}
    drops = {d.frame.frame_id for d in result.drops}
    assert not outputs & drops
    assert outputs | drops == {f.frame_id for f in result.frames}
    assert len(drops) == len(result.drops)
    m = result.metrics
    assert m.frames_produced == m.frames_consumed + m.frames_dropped
    assert m.frames_processed >= m.frames_consumed
    assert (
        m.frames_replaced + m.frames_rejected + m.frames_invalidated <= m.frames_dropped
    )
    if filtered:
        assert m.obsolete_session_outputs == 0
        assert all(
            e.frame.session_id == e.session_id
            for e in result.events
            if e.kind == "frame_consumed"
        )
    assert [e.at_ms for e in result.events] == sorted(e.at_ms for e in result.events)
    assert all(
        p.age_at_completion_ms >= p.age_at_start_ms >= 0 for p in result.processing
    )
    if policy == "latest":
        assert m.max_queue_depth <= 1


def test_every_recovery_workload_and_comparison_is_deterministic(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("recovery experiments must remain virtual and offline")

    for name in ("time.sleep", "time.time", "time.monotonic", "socket.socket"):
        monkeypatch.setattr(name, forbidden)
    for config in RECOVERY_SCENARIOS.values():
        for policy in ("fifo", "latest"):
            for filtered in (False, True):
                workload = replace(config, policy=policy, session_filter=filtered)
                expected = Simulator(workload).run().to_dict()
                for _ in range(100):
                    assert Simulator(workload).run().to_dict() == expected


@pytest.mark.parametrize(
    "config", RECOVERY_SCENARIOS.values(), ids=RECOVERY_SCENARIOS.keys()
)
def test_identical_source_evidence_across_all_comparison_modes(config) -> None:
    reference = Simulator(replace(config, policy="fifo", session_filter=False)).run()
    for policy in ("fifo", "latest"):
        for filtered in (False, True):
            result = Simulator(
                replace(config, policy=policy, session_filter=filtered)
            ).run()
            assert result.frames == reference.frames


def test_new_epoch_at_watchdog_deadline_resets_monitor_baseline() -> None:
    result = Simulator(
        Config(
            no_progress_timeout_ms=25,
            controls=(Control(25, "disconnect"), Control(45, "reconnect")),
        )
    ).run()
    # Last epoch-0 production is 20; reconnect at its 45 ms deadline wins.
    assert result.metrics.no_progress_intervals == 0
    assert next(e.at_ms for e in result.events if e.kind == "stream_recovered") == 45


@pytest.mark.parametrize(
    "controls",
    [
        (Control(0, "reconnect"),),
        (Control(0, "unfreeze"),),
        (Control(0, "disconnect"), Control(1, "disconnect")),
        (Control(0, "freeze"), Control(1, "freeze")),
        (Control(0, "disconnect"), Control(1, "freeze")),
        (Control(2, "freeze"), Control(1, "unfreeze")),
        (Control(100, "disconnect"),),
        [Control(1, "freeze")],
        ("freeze",),
    ],
)
def test_invalid_control_lifecycle_and_order(controls) -> None:
    with pytest.raises(ValueError):
        Config(controls=controls)


@pytest.mark.parametrize(
    "values",
    [
        (0, "unknown", None),
        (-1, "freeze", None),
        (1, "slowdown", None),
        (1, "slowdown", 0),
        (1, "freeze", 10),
    ],
)
def test_invalid_control_values(values) -> None:
    with pytest.raises(ValueError):
        Control(*values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"session_filter": 1},
        {"queue_on_disconnect": "unknown"},
        {"no_progress_timeout_ms": 0},
        {"no_progress_timeout_ms": True},
    ],
)
def test_invalid_recovery_config(overrides) -> None:
    with pytest.raises(ValueError):
        Config(**overrides)


def test_cli_recovery_json_and_policy_selection() -> None:
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "video_freshness_lab",
            "--suite",
            "recovery",
            "--scenario",
            "reconnect",
            "--policy",
            "latest",
            "--session-filter",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(run.stdout)["reconnect"]
    assert data["schema_version"] == 2
    assert data["config"]["policy"] == "latest" and data["config"]["session_filter"]
    assert data["metrics"]["obsolete_session_outputs"] == 0
    assert data["metrics"]["frames_rejected"] == 2
