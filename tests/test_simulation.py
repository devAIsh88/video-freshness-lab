import json
import subprocess
import sys
from dataclasses import replace

import pytest

from video_freshness_lab.clock import VirtualClock
from video_freshness_lab.experiments import SCENARIOS
from video_freshness_lab.simulation import Config, Simulator


def test_balanced_schedule_order_and_termination() -> None:
    clock = VirtualClock()
    result = Simulator(Config(duration_ms=40), clock).run()
    assert [f.frame_id for f in result.frames] == [
        f"epoch-0/frame-{i}" for i in range(4)
    ]
    assert [p.started_at_ms for p in result.processing] == [0, 10, 20, 30]
    assert [p.completed_at_ms for p in result.processing] == [10, 20, 30, 40]
    assert [p.age_at_start_ms for p in result.processing] == [0] * 4
    assert [p.lag_at_completion for p in result.processing] == [0] * 4
    assert result.metrics.frames_produced == result.metrics.frames_consumed == 4
    assert result.metrics.max_queue_depth == 1
    assert result.metrics.finished_at_ms == 40 and clock.pending_count == 0
    at_ten = [e.kind for e in result.events if e.at_ms == 10]
    assert at_ten == [
        "frame_consumed",
        "frame_produced",
        "frame_queued",
        "processing_started",
    ]


def test_fifo_slow_consumer_ages_lag_and_completion() -> None:
    result = Simulator(Config(duration_ms=40, consumer_duration_ms=25)).run()
    assert [p.frame.sequence for p in result.processing] == [0, 1, 2, 3]
    assert [p.age_at_start_ms for p in result.processing] == [0, 15, 30, 45]
    assert [p.age_at_completion_ms for p in result.processing] == [25, 40, 55, 70]
    assert [p.lag_at_start for p in result.processing] == [0, 1, 1, 0]
    assert [p.lag_at_completion for p in result.processing] == [2, 2, 1, 0]
    m = result.metrics
    assert m.finished_at_ms == 100 and m.max_queue_depth == 2
    assert m.mean_start_age_ms == 22.5 and m.mean_completion_age_ms == 47.5
    assert m.start_freshness_violations == 1 and m.result_freshness_violations == 3


def test_latest_drop_accounting_and_active_work() -> None:
    result = Simulator(
        Config(duration_ms=40, consumer_duration_ms=25, policy="latest")
    ).run()
    assert [p.frame.sequence for p in result.processing] == [0, 2, 3]
    assert [p.age_at_start_ms for p in result.processing] == [0, 5, 20]
    assert [p.age_at_completion_ms for p in result.processing] == [25, 30, 45]
    assert [d.frame.sequence for d in result.drops] == [1]
    assert result.drops[0].at_ms == 20
    assert result.metrics.frames_dropped == result.metrics.frames_replaced == 1
    assert result.metrics.frames_consumed == 3 and result.metrics.finished_at_ms == 75


@pytest.mark.parametrize(
    ("threshold", "violations"), [(9, 1), (10, 0), (11, 0), (None, 0)]
)
def test_result_freshness_threshold_boundary(threshold, violations) -> None:
    result = Simulator(Config(duration_ms=1, freshness_threshold_ms=threshold)).run()
    assert result.metrics.result_freshness_violations == violations
    assert result.metrics.start_freshness_violations == 0


def test_equal_workload_comparison_and_in_progress_limit() -> None:
    fifo = Simulator(SCENARIOS["slowdown-fifo"]).run()
    latest = Simulator(SCENARIOS["slowdown-latest"]).run()
    assert fifo.frames == latest.frames
    assert fifo.metrics.max_start_age_ms == 270
    assert latest.metrics.max_start_age_ms == 30
    assert fifo.metrics.max_completion_age_ms == 310
    assert latest.metrics.max_completion_age_ms == 70
    # A latest-frame dequeue still cannot cancel expensive processing.
    strict = Simulator(
        replace(SCENARIOS["slowdown-latest"], freshness_threshold_ms=30)
    ).run()
    assert strict.metrics.start_freshness_violations == 0
    assert strict.metrics.result_freshness_violations == 4


@pytest.mark.parametrize("policy", ["fifo", "latest"])
@pytest.mark.parametrize("consumer_ms", [1, 10, 25, 40])
@pytest.mark.parametrize("overflow", ["drop_newest", "drop_oldest"])
def test_exact_conservation_and_finite_drain(policy, consumer_ms, overflow) -> None:
    config = Config(
        policy=policy,
        consumer_duration_ms=consumer_ms,
        queue_capacity=1,
        overflow=overflow,
    )
    result = Simulator(config).run()
    consumed = {p.frame.frame_id for p in result.processing}
    dropped = {d.frame.frame_id for d in result.drops}
    assert not consumed & dropped
    assert consumed | dropped == {f.frame_id for f in result.frames}
    assert len(dropped) == len(result.drops)
    assert (
        result.metrics.frames_produced
        == result.metrics.frames_consumed + result.metrics.frames_dropped
    )
    assert (
        result.metrics.finished_at_ms
        <= config.duration_ms + len(result.frames) * consumer_ms
    )
    assert result.metrics.max_queue_depth <= 1


def test_reproducible_hundred_runs_without_wall_clock(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("simulation must not access wall-clock or network")

    monkeypatch.setattr("time.sleep", forbidden)
    monkeypatch.setattr("time.time", forbidden)
    monkeypatch.setattr("time.monotonic", forbidden)
    monkeypatch.setattr("socket.socket", forbidden)
    for config in SCENARIOS.values():
        expected = Simulator(config).run().to_dict()
        for _ in range(100):
            assert Simulator(config).run().to_dict() == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"duration_ms": 0},
        {"duration_ms": 1.5},
        {"producer_interval_ms": -1},
        {"consumer_duration_ms": True},
        {"policy": "unknown"},
        {"queue_capacity": 0},
        {"overflow": "unknown"},
        {"freshness_threshold_ms": -1},
        {"policy": "latest", "queue_capacity": 2},
    ],
)
def test_invalid_config(overrides) -> None:
    with pytest.raises(ValueError):
        Config(**overrides)


def test_single_run_and_fresh_clock_requirement() -> None:
    simulator = Simulator(Config())
    simulator.run()
    with pytest.raises(ValueError, match="only once"):
        simulator.run()
    clock = VirtualClock()
    clock.run_until(1)
    with pytest.raises(ValueError, match="fresh"):
        Simulator(Config(), clock)


def test_installed_cli_json_and_invalid_input() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "video_freshness_lab", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(completed.stdout)
    assert set(data) == set(SCENARIOS)
    assert data["balanced"]["timestamp_units"] == "ms"
    assert data["balanced"]["metrics"]["frames_consumed"] == 10
    bad = subprocess.run(
        [sys.executable, "-m", "video_freshness_lab", "--duration-ms", "0"],
        capture_output=True,
        text=True,
    )
    assert bad.returncode == 2 and "duration_ms" in bad.stderr
