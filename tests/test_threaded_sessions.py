from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from threading import Barrier, Event, Lock, Thread
from time import monotonic

import pytest

from video_freshness_lab.model import Frame
from video_freshness_lab.threaded_demo import (
    ShutdownTimeout,
    WorkerFailed,
    WorkerFailure,
)
from video_freshness_lab.threaded_mailbox import MailboxClosed
from video_freshness_lab.threaded_sessions import SessionPipeline

GUARD_S = 5.0


def wait(event):
    assert event.wait(GUARD_S), "coordination event did not arrive"


def process(frame, stop):
    return frame.sequence


class Workers:
    """Test owner: surface failures and always join explicit non-daemon threads."""

    def __init__(self, pipeline, source=None, callback=process):
        self.pipeline = pipeline
        self.stop = Event()
        self.failures = []
        self.lock = Lock()
        self.threads = [
            Thread(
                target=self.capture,
                args=("consumer", pipeline.consume, callback, self.stop),
                daemon=False,
            )
        ]
        if source is not None:
            self.threads.append(
                Thread(
                    target=self.capture,
                    args=("producer", pipeline.run_producer, source, self.stop),
                    daemon=False,
                )
            )

    def capture(self, role, run, *args):
        try:
            run(*args)
        except BaseException as error:
            with self.lock:
                self.failures.append(WorkerFailure(role, error))

    def start(self):
        for thread in self.threads:
            thread.start()

    def join(self, timeout=GUARD_S):
        deadline = monotonic() + timeout
        for thread in self.threads:
            thread.join(max(0, deadline - monotonic()))
        alive = tuple(t.name for t in self.threads if t.is_alive())
        if alive:
            raise ShutdownTimeout(alive)
        if self.failures:
            raise WorkerFailed(tuple(self.failures)) from self.failures[0].error

    def cleanup(self):
        self.pipeline.shutdown()
        self.stop.set()
        deadline = monotonic() + GUARD_S
        for thread in self.threads:
            if thread.ident is not None:
                thread.join(max(0, deadline - monotonic()))
        assert not any(t.is_alive() for t in self.threads)


@contextmanager
def workers(pipeline, source=None, callback=process):
    group = Workers(pipeline, source, callback)
    try:
        group.start()
        yield group
    finally:
        group.cleanup()


def ledger(state, *, drained=True):
    mailbox = state.mailbox
    assert state.produced == mailbox.accepted
    assert mailbox.accepted == mailbox.replaced + mailbox.pending + state.acquired
    assert (
        state.acquired == state.processed + state.processing_failed + state.in_progress
    )
    assert state.processed == (
        state.published + state.rejected_obsolete + state.discarded_shutdown
    )
    assert len({c.result.frame.frame_id for c in state.completions}) == state.processed
    assert len(state.outputs) == state.published
    assert [event.order for event in state.events] == list(range(len(state.events)))
    if drained:
        assert mailbox.pending == state.in_progress == 0


def test_normal_single_session_preserves_identity_and_result(monkeypatch):
    pipeline = SessionPipeline()
    published = Event()
    real_complete = pipeline.complete

    def observe_completion(frame, value):
        decision = real_complete(frame, value)
        if frame.sequence == 0:
            published.set()
        return decision

    monkeypatch.setattr(pipeline, "complete", observe_completion)

    def source(pipe, stop):
        first = pipe.produce(17)
        wait(published)
        assert pipe.snapshot().outputs[0].frame is first
        pipe.produce(18)

    def calculate(frame, stop):
        return frame.sequence + 100

    with workers(pipeline, source, calculate) as group:
        group.join()
    state = pipeline.snapshot()
    ledger(state)
    assert state.published == state.processed == 2
    assert [r.value for r in state.outputs] == [100, 101]
    assert [r.frame.produced_at_ms for r in state.outputs] == [17, 18]


@pytest.mark.parametrize("produce_new", [False, True])
def test_transition_retains_waiting_frame_unless_replaced(produce_new):
    pipeline = SessionPipeline()
    old = pipeline.produce()
    pipeline.transition()
    assert pipeline.snapshot().mailbox.pending == 1
    if produce_new:
        newest = pipeline.produce()
    pipeline.close()
    with workers(pipeline) as group:
        group.join()
    state = pipeline.snapshot()
    ledger(state)
    assert state.processed == 1
    assert state.mailbox.replaced == int(produce_new)
    assert state.rejected_obsolete == int(not produce_new)
    assert state.published == int(produce_new)
    assert state.completions[0].result.frame is (newest if produce_new else old)


def in_flight_transition(cycles):
    pipeline = SessionPipeline()
    acquired, release, newer_produced = Event(), Event(), Event()

    def calculate(frame, stop):
        if frame.session_id == 0:
            acquired.set()
            wait(release)
        return frame.sequence + 100

    def source(pipe, stop):
        pipe.produce(1)
        wait(acquired)
        for _ in range(cycles):
            pipe.transition()
            pipe.produce(2)
        newer_produced.set()

    with workers(pipeline, source, calculate) as group:
        try:
            wait(newer_produced)
            paused = pipeline.snapshot()
            ledger(paused, drained=False)
            assert paused.epoch == cycles and paused.processed == paused.published == 0
            assert paused.in_progress == 1 and paused.mailbox.pending == 1
            release.set()
            group.join()
        finally:
            release.set()
    state = pipeline.snapshot()
    ledger(state)
    assert state.processed == 2 and state.rejected_obsolete == state.published == 1
    assert state.mailbox.replaced == cycles - 1
    assert state.outputs[0].frame.session_id == cycles
    old_completion = state.completions[0]
    assert old_completion.result.frame.session_id == 0
    assert (
        old_completion.current_epoch == cycles and old_completion.outcome == "obsolete"
    )
    assert old_completion.result.value == 100
    events = state.events
    obsolete = next(e.order for e in events if e.kind == "obsolete")
    latest_production = max(e.order for e in events if e.kind == "produced")
    assert latest_production < obsolete
    return state


@pytest.mark.parametrize("cycles", [1, 3, 10])
def test_obsolete_active_result_is_suppressed_after_newer_production(cycles):
    in_flight_transition(cycles)


def test_hundred_fresh_session_lifecycles_with_repeated_transitions():
    for _ in range(100):
        in_flight_transition(3)


def test_transition_without_new_production_still_invalidates_active_result():
    pipeline = SessionPipeline()
    frame = pipeline.produce()
    assert pipeline.acquire() is frame
    pipeline.transition()
    decision = pipeline.complete(frame, 7)
    assert decision.outcome == "obsolete"
    ledger(pipeline.snapshot())


@pytest.mark.parametrize("pending", [False, True])
def test_shutdown_with_active_or_pending_frame_drains_and_suppresses(pending):
    pipeline = SessionPipeline()
    entered = Event()

    def calculate(frame, stop):
        if frame.sequence == 0:
            entered.set()
            wait(stop)
        return frame.sequence

    with workers(pipeline, callback=calculate) as group:
        pipeline.produce()
        wait(entered)
        if pending:
            pipeline.produce()
        pipeline.shutdown()
        group.stop.set()
        group.join()
        state = pipeline.snapshot()
        pipeline.shutdown()
        assert pipeline.snapshot() == state
    ledger(state)
    assert state.processed == state.discarded_shutdown == 1 + int(pending)
    assert state.published == state.rejected_obsolete == state.processing_failed == 0


def test_close_only_permits_current_epoch_result_after_drain():
    pipeline = SessionPipeline()
    frame = pipeline.produce()
    pipeline.close()
    closed = pipeline.snapshot()
    pipeline.close()
    assert pipeline.snapshot() == closed
    assert pipeline.acquire() is frame
    assert pipeline.complete(frame, 99).outcome == "published"
    with pytest.raises(MailboxClosed):
        pipeline.acquire()
    ledger(pipeline.snapshot())


def test_shutdown_empty_wakes_blocked_consumer():
    pipeline = SessionPipeline()
    with workers(pipeline) as group:
        assert pipeline.wait_until_waiting(GUARD_S)
        pipeline.shutdown()
        group.stop.set()
        group.join()
    ledger(pipeline.snapshot())


def test_close_and_transition_race_retains_queue_without_reopening():
    for _ in range(50):
        pipeline = SessionPipeline()
        pipeline.produce()
        barrier = Barrier(2, timeout=GUARD_S)
        failures = []

        def change(pipe, rendezvous, errors):
            try:
                rendezvous.wait()
                pipe.transition()
            except BaseException as error:
                errors.append(error)

        thread = Thread(target=change, args=(pipeline, barrier, failures), daemon=False)
        thread.start()
        try:
            barrier.wait()
            pipeline.close()
        finally:
            thread.join(GUARD_S)
            assert not thread.is_alive()
        assert not failures
        before_drain = pipeline.snapshot()
        assert before_drain.epoch == before_drain.mailbox.pending == 1
        assert before_drain.mailbox.closed
        with workers(pipeline) as group:
            group.join()
        state = pipeline.snapshot()
        ledger(state)
        assert state.epoch == 1 and state.mailbox.closed
        with pytest.raises(MailboxClosed):
            pipeline.produce()
        assert state.rejected_obsolete == 1 and state.published == 0


@pytest.mark.parametrize("transition_first", [False, True])
def test_ordered_transition_and_final_delivery_boundary(transition_first):
    pipeline = SessionPipeline()
    frame = pipeline.produce()
    pipeline.acquire()
    if transition_first:
        pipeline.transition()
    decision = pipeline.complete(frame, 0)
    if not transition_first:
        pipeline.transition()
    assert decision.outcome == ("obsolete" if transition_first else "published")
    # Earlier published history is not retracted when the active epoch changes.
    assert pipeline.snapshot().published == int(not transition_first)
    ledger(pipeline.snapshot())


def test_unordered_transition_publication_race_has_only_valid_linearizations():
    for _ in range(50):
        pipeline = SessionPipeline()
        frame = pipeline.produce()
        pipeline.acquire()
        barrier = Barrier(2, timeout=GUARD_S)
        failures = []

        def finish(pipe, active, rendezvous, errors):
            try:
                rendezvous.wait()
                pipe.complete(active, 0)
            except BaseException as error:
                errors.append(error)

        thread = Thread(
            target=finish, args=(pipeline, frame, barrier, failures), daemon=False
        )
        thread.start()
        try:
            barrier.wait()
            pipeline.transition()
        finally:
            thread.join(GUARD_S)
            assert not thread.is_alive()
        assert not failures
        state = pipeline.snapshot()
        ledger(state)
        decision = state.completions[0]
        if decision.outcome == "published":
            assert decision.current_epoch == 0
            published_order = next(
                e.order for e in state.events if e.kind == "published"
            )
            started_order = next(
                e.order
                for e in state.events
                if e.kind == "session_started" and e.epoch == 1
            )
            assert published_order < started_order
        else:
            assert decision.outcome == "obsolete" and decision.current_epoch == 1


@pytest.mark.parametrize("role", ["producer", "consumer"])
def test_worker_exception_during_transition_is_reported_with_exact_accounting(role):
    pipeline = SessionPipeline()
    acquired, transitioned = Event(), Event()
    failure = OSError("synthetic processing failure")

    def source(pipe, stop):
        pipe.produce()
        wait(acquired)
        pipe.transition()
        transitioned.set()
        if role == "producer":
            raise failure

    def calculate(frame, stop):
        acquired.set()
        wait(transitioned)
        if role == "consumer":
            raise failure
        wait(stop)
        return 0

    with workers(pipeline, source, calculate) as group:
        with pytest.raises(WorkerFailed) as error:
            group.join()
        assert error.value.__cause__ is failure
        assert error.value.failures[0].role == role
        assert group.stop.is_set()
    state = pipeline.snapshot()
    ledger(state)
    assert state.shutdown and state.published == 0
    assert state.processing_failed == int(role == "consumer")
    assert state.discarded_shutdown == int(role == "producer")


def test_failed_processing_preserves_pending_item_for_owner_drainage():
    pipeline = SessionPipeline()
    entered, release = Event(), Event()

    def fail(frame, stop):
        entered.set()
        wait(release)
        raise ValueError("synthetic failure")

    with workers(pipeline, callback=fail) as group:
        try:
            pipeline.produce()
            wait(entered)
            pipeline.produce()
            pipeline.transition()
            release.set()
            with pytest.raises(WorkerFailed):
                group.join()
        finally:
            release.set()
    state = pipeline.snapshot()
    ledger(state, drained=False)
    assert state.mailbox.pending == state.processing_failed == 1
    frame = pipeline.acquire()
    assert pipeline.complete(frame, 1).outcome == "shutdown"
    ledger(pipeline.snapshot())


def test_invalid_inputs_duplicate_completion_and_forged_identity_do_not_count():
    pipeline = SessionPipeline()
    before = pipeline.snapshot()
    with pytest.raises(ValueError):
        pipeline.fail_processing(None)
    with pytest.raises(ValueError):
        pipeline.complete(None, 1)
    assert pipeline.snapshot() == before
    with pytest.raises(ValueError):
        pipeline.produce(-1)
    assert pipeline.snapshot() == before
    frame = pipeline.produce()
    assert pipeline.acquire() is frame
    with pytest.raises(RuntimeError):
        pipeline.acquire(0)
    with pytest.raises(ValueError):
        pipeline.complete(Frame(0, 0, 0), 1)
    with pytest.raises(TypeError):
        pipeline.complete(frame, True)
    pipeline.complete(frame, 1)
    with pytest.raises(ValueError):
        pipeline.complete(frame, 1)
    with pytest.raises(FrozenInstanceError):
        pipeline.snapshot().outputs[0].value = 9
    with pytest.raises(FrozenInstanceError):
        pipeline.snapshot().epoch = 10
    ledger(pipeline.snapshot())


def test_empty_timeout_resets_consumer_reservation_and_shutdown_rejects_transition():
    pipeline = SessionPipeline()
    with pytest.raises(TimeoutError):
        pipeline.acquire(0)
    pipeline.produce()
    frame = pipeline.acquire()
    pipeline.shutdown()
    with pytest.raises(RuntimeError):
        pipeline.transition()
    with pytest.raises(MailboxClosed):
        pipeline.produce()
    assert pipeline.complete(frame, 0).outcome == "shutdown"
    ledger(pipeline.snapshot())


def test_current_epoch_does_not_imply_an_age_based_freshness_policy():
    pipeline = SessionPipeline()
    frame = pipeline.produce(0)
    pipeline.acquire()
    assert pipeline.complete(frame, 0).outcome == "published"
    # No clock/budget is supplied: provenance success is not a freshness verdict.
    ledger(pipeline.snapshot())


def test_noninteger_processing_result_is_failure_not_success_or_obsolete_rejection():
    pipeline = SessionPipeline()
    pipeline.produce()
    pipeline.close()
    with workers(pipeline, callback=lambda frame, stop: True) as group:
        with pytest.raises(WorkerFailed) as error:
            group.join()
        assert isinstance(error.value.__cause__, TypeError)
    state = pipeline.snapshot()
    ledger(state)
    assert state.processing_failed == 1
    assert state.processed == state.published == state.rejected_obsolete == 0
