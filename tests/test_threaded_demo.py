import json
import subprocess
import sys
from threading import Event, Thread

import pytest

from video_freshness_lab.threaded_demo import (
    DemoConfig,
    ShutdownTimeout,
    ThreadedDemo,
    WorkerFailed,
    run_demo,
)

GUARD_S = 5.0


def cleanup(demo: ThreadedDemo) -> None:
    demo.stop()
    demo._join_workers(GUARD_S)
    assert not demo.alive_workers


@pytest.mark.parametrize("mode", ["normal", "slow"])
@pytest.mark.parametrize("count", [0, 1, 2, 10])
def test_coordinated_production_delivery_replacement_and_shutdown(mode, count) -> None:
    result = run_demo(DemoConfig(mode, count), GUARD_S)
    expected = list(range(count)) if mode == "normal" or count < 2 else [0, count - 1]
    assert [f.sequence for f in result.delivered_frames] == expected
    assert len({f.frame_id for f in result.delivered_frames}) == len(expected)
    assert [f.produced_at_ms for f in result.delivered_frames] == sorted(
        f.produced_at_ms for f in result.delivered_frames
    )
    state = result.mailbox
    assert result.produced == state.accepted == count
    assert result.rejected_submissions == 0
    assert state.delivered == len(expected) and state.replaced == count - len(expected)
    assert state.closed and state.pending == state.waiting_consumers == 0
    assert (
        result.producer_finished
        and result.consumer_finished
        and result.threads_terminated
    )


def test_idle_stop_wakes_empty_consumer_and_idle_producer() -> None:
    demo = ThreadedDemo(DemoConfig("idle", 0))
    demo.start()
    try:
        assert demo.mailbox.wait_until_waiting(GUARD_S)
        assert len(demo.alive_workers) == 2
        result = demo.shutdown(GUARD_S)
        assert result.producer_finished and result.consumer_finished
        assert result.mailbox.closed and result.mailbox.pending == 0
        assert result.mailbox.accepted == 0
        assert demo.shutdown(GUARD_S) == result
    finally:
        cleanup(demo)


def test_workers_are_explicitly_non_daemon() -> None:
    demo = ThreadedDemo()
    assert not demo._producer.daemon and not demo._consumer.daemon


def test_stop_submit_race_reports_constructed_but_rejected_frame() -> None:
    demo = ThreadedDemo(DemoConfig("normal", 1))
    original_submit = demo.mailbox.submit

    def close_before_submit(frame):
        demo.stop()
        return original_submit(frame)

    demo.mailbox.submit = close_before_submit
    demo.start()
    try:
        result = demo.join(GUARD_S)
        assert result.produced == result.rejected_submissions == 1
        assert result.mailbox.accepted == result.mailbox.delivered == 0
        assert result.mailbox.closed and result.mailbox.pending == 0
    finally:
        cleanup(demo)


def test_shutdown_with_pending_frame_and_cooperative_active_consumer() -> None:
    processing = Event()

    def hold_first(frame, stop) -> None:
        if frame.sequence == 0:
            processing.set()
            stop.wait()

    demo = ThreadedDemo(DemoConfig("normal", 2), process=hold_first)
    accepted_second = Event()
    real_submit = demo.mailbox.submit

    def observe_submission(frame):
        replaced = real_submit(frame)
        if frame.sequence == 1:
            accepted_second.set()
        return replaced

    demo.mailbox.submit = observe_submission
    demo.start()
    try:
        assert processing.wait(GUARD_S) and accepted_second.wait(GUARD_S)
        assert demo.mailbox.snapshot().pending == 1
        result = demo.shutdown(GUARD_S)
        assert [f.sequence for f in result.delivered_frames] == [0, 1]
        assert result.mailbox.pending == 0 and result.mailbox.replaced == 0
        assert result.threads_terminated
    finally:
        cleanup(demo)


def test_shutdown_wakes_producer_waiting_for_acknowledgement() -> None:
    parked = Event()

    def park_consumer(demo) -> None:
        parked.set()
        demo._stop.wait()

    demo = ThreadedDemo(DemoConfig("normal", 1))
    demo._consume = lambda: park_consumer(demo)
    submitted = Event()
    real_submit = demo.mailbox.submit

    def observe(frame):
        value = real_submit(frame)
        submitted.set()
        return value

    demo.mailbox.submit = observe
    # Thread targets store _worker; the bound run argument was created in __init__.
    # Install the deliberate parked worker explicitly before any start.
    demo._consumer = Thread(
        target=demo._worker, args=("consumer", demo._consume), daemon=False
    )
    demo.start()
    try:
        assert parked.wait(GUARD_S) and submitted.wait(GUARD_S)
        result = demo.shutdown(GUARD_S)
        assert result.producer_finished and result.consumer_finished
        assert (
            result.mailbox.pending == 1
        )  # Parked test consumer deliberately did not drain.
        assert demo.mailbox.get().sequence == 0
    finally:
        cleanup(demo)


@pytest.mark.parametrize("role", ["producer", "consumer"])
def test_worker_exceptions_reach_owner_and_stop_peer(role) -> None:
    failure = ValueError("synthetic worker failure")

    def fail(*args):
        raise failure

    demo = ThreadedDemo(
        DemoConfig("normal", 5), process=fail if role == "consumer" else None
    )
    if role == "producer":
        demo._producer = Thread(
            target=demo._worker,
            args=("producer", fail),
            name="freshness-producer",
            daemon=False,
        )
    demo.start()
    try:
        with pytest.raises(WorkerFailed) as error:
            demo.join(GUARD_S)
        assert error.value.__cause__ is failure
        assert error.value.failures[0].role == role
        assert demo.producer_finished.is_set() and demo.consumer_finished.is_set()
        assert not demo.alive_workers
        state = demo.mailbox.snapshot()
        assert state.accepted == state.delivered + state.replaced + state.pending
    finally:
        cleanup(demo)


def test_join_reports_uncooperative_callback_and_test_releases_it() -> None:
    entered, release = Event(), Event()

    def uncooperative(frame, stop) -> None:
        entered.set()
        release.wait()

    demo = ThreadedDemo(DemoConfig("normal", 1), process=uncooperative)
    demo.start()
    try:
        assert entered.wait(GUARD_S)
        with pytest.raises(ShutdownTimeout) as error:
            demo.shutdown(0.01)
        assert "freshness-consumer" in error.value.alive_workers
        assert demo.mailbox.snapshot().closed
    finally:
        release.set()
        cleanup(demo)
    assert demo.join(GUARD_S).threads_terminated


@pytest.mark.parametrize("role", ["producer", "consumer"])
def test_partial_startup_failure_cleans_started_worker(monkeypatch, role) -> None:
    real_start = Thread.start

    def fail_start(thread):
        if thread.name == f"freshness-{role}":
            raise OSError("synthetic startup failure")
        return real_start(thread)

    monkeypatch.setattr(Thread, "start", fail_start)
    demo = ThreadedDemo()
    with pytest.raises(OSError):
        demo.start()
    assert not demo.alive_workers and demo.mailbox.snapshot().closed
    with pytest.raises(WorkerFailed, match="startup"):
        demo.join(GUARD_S)
    cleanup(demo)


def test_closed_lifecycle_cannot_be_restarted() -> None:
    stopped = ThreadedDemo()
    stopped.stop()
    with pytest.raises(ValueError):
        stopped.start()
    with pytest.raises(ValueError):
        stopped.join()
    demo = ThreadedDemo()
    demo.start()
    try:
        demo.join(GUARD_S)
        with pytest.raises(ValueError):
            demo.start()
    finally:
        cleanup(demo)


def test_invalid_join_budget_does_not_close_running_demo() -> None:
    demo = ThreadedDemo(DemoConfig("idle", 0))
    demo.start()
    try:
        assert demo.mailbox.wait_until_waiting(GUARD_S)
        with pytest.raises(ValueError):
            demo.shutdown(0)
        assert not demo.mailbox.snapshot().closed
    finally:
        cleanup(demo)


def test_hundred_repeated_fresh_lifecycles_are_joined() -> None:
    for _ in range(100):
        for config in (
            DemoConfig("normal", 5),
            DemoConfig("slow", 5),
            DemoConfig("idle", 0),
        ):
            result = run_demo(config, GUARD_S)
            assert (
                result.threads_terminated
                and result.producer_finished
                and result.consumer_finished
            )
            assert result.mailbox.closed and result.mailbox.pending == 0


@pytest.mark.parametrize(
    "config",
    [{"items": -1}, {"items": True}, {"mode": "unknown"}, {"mode": "idle", "items": 1}],
)
def test_invalid_demo_config(config) -> None:
    with pytest.raises(ValueError):
        DemoConfig(**config)


@pytest.mark.parametrize("mode", ["normal", "slow", "idle"])
def test_installed_threaded_cli(mode) -> None:
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "video_freshness_lab.threaded_demo",
            "--mode",
            mode,
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=GUARD_S,
        check=True,
    )
    data = json.loads(process.stdout)
    assert (
        data["threads_terminated"]
        and data["producer_finished"]
        and data["consumer_finished"]
    )
    assert data["mailbox"]["closed"] and data["mailbox"]["pending"] == 0
    assert data["mailbox"]["replaced"] == (8 if mode == "slow" else 0)
