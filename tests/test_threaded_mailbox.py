from dataclasses import FrozenInstanceError
from threading import TIMEOUT_MAX, Barrier, Event, Thread

import pytest

from video_freshness_lab.model import Frame
from video_freshness_lab.threaded_mailbox import LatestFrameMailbox, MailboxClosed

GUARD_S = 5.0


def join(thread: Thread) -> None:
    thread.join(GUARD_S)
    assert not thread.is_alive(), f"test worker did not terminate: {thread.name}"


def capture_get(mailbox, result) -> None:
    try:
        result.append(mailbox.get())
    except BaseException as error:
        result.append(error)


def test_empty_poll_and_positive_timeout_leave_counters_unchanged() -> None:
    mailbox = LatestFrameMailbox()
    initial = mailbox.snapshot()
    with pytest.raises(TimeoutError):
        mailbox.get(timeout_s=0)
    with pytest.raises(TimeoutError):
        mailbox.get(timeout_s=0.001)
    assert mailbox.snapshot() == initial
    assert not mailbox.wait_until_waiting(0)


def test_retrieval_transfers_identity_once_and_frame_is_immutable() -> None:
    mailbox = LatestFrameMailbox()
    frame = Frame(0, 0, 5)
    assert mailbox.submit(frame) is None
    assert mailbox.get(timeout_s=0) is frame
    with pytest.raises(FrozenInstanceError):
        frame.sequence = 1
    with pytest.raises(TimeoutError):
        mailbox.get(timeout_s=0)
    state = mailbox.snapshot()
    assert (state.accepted, state.delivered, state.replaced, state.pending) == (
        1,
        1,
        0,
        0,
    )
    with pytest.raises(FrozenInstanceError):
        state.accepted = 2


def test_replacement_returns_displaced_item_and_tracks_all_drops() -> None:
    mailbox = LatestFrameMailbox()
    frames = [Frame(0, i, i) for i in range(4)]
    assert mailbox.submit(frames[0]) is None
    for i in range(1, 4):
        assert mailbox.submit(frames[i]) is frames[i - 1]
    assert mailbox.get(timeout_s=0) is frames[-1]
    state = mailbox.snapshot()
    assert (state.accepted, state.delivered, state.replaced, state.pending) == (
        4,
        1,
        3,
        0,
    )


def test_strict_identity_order_survives_drain_and_accepts_new_epoch() -> None:
    mailbox = LatestFrameMailbox()
    first = Frame(0, 2, 0)
    mailbox.submit(first)
    mailbox.get()
    for frame in (first, Frame(0, 1, 1)):
        with pytest.raises(ValueError, match="strictly increase"):
            mailbox.submit(frame)
    second = Frame(1, 0, 2)
    mailbox.submit(second)
    with pytest.raises(ValueError):
        mailbox.submit(Frame(0, 100, 3))
    assert mailbox.get() is second
    assert mailbox.snapshot().accepted == 2


def test_invalid_frame_does_not_replace_existing_evidence() -> None:
    mailbox = LatestFrameMailbox()
    frame = Frame(0, 0, 0)
    mailbox.submit(frame)
    with pytest.raises(TypeError):
        mailbox.submit(object())
    assert mailbox.get() is frame
    assert mailbox.snapshot().replaced == 0


def test_close_drains_pending_once_and_is_idempotent() -> None:
    mailbox = LatestFrameMailbox()
    frame = Frame(0, 0, 0)
    mailbox.submit(frame)
    mailbox.close()
    closed = mailbox.snapshot()
    assert closed.closed and closed.pending == 1
    mailbox.close()
    assert mailbox.snapshot() == closed
    with pytest.raises(MailboxClosed):
        mailbox.submit(Frame(0, 1, 1))
    with pytest.raises(MailboxClosed):
        mailbox.submit(None)
    assert mailbox.snapshot() == closed
    assert mailbox.get() is frame
    with pytest.raises(MailboxClosed):
        mailbox.get()
    assert mailbox.snapshot().pending == 0
    assert mailbox.snapshot().accepted == mailbox.snapshot().delivered == 1


def test_close_empty_makes_future_gets_immediate() -> None:
    mailbox = LatestFrameMailbox()
    mailbox.close()
    for _ in range(3):
        with pytest.raises(MailboxClosed):
            mailbox.get()
    assert not mailbox.wait_until_waiting(GUARD_S)


@pytest.mark.parametrize("action", ["submit", "close"])
def test_blocked_consumer_is_notified_without_lost_wakeup(action) -> None:
    mailbox = LatestFrameMailbox()
    result = []
    consumer = Thread(target=capture_get, args=(mailbox, result), daemon=False)
    consumer.start()
    try:
        assert mailbox.wait_until_waiting(GUARD_S)
        assert mailbox.snapshot().waiting_consumers == 1
        frame = Frame(0, 0, 0)
        if action == "submit":
            mailbox.submit(frame)
        else:
            mailbox.close()
        join(consumer)
        assert len(result) == 1
        assert (
            result[0] is frame
            if action == "submit"
            else isinstance(result[0], MailboxClosed)
        )
    finally:
        mailbox.close()
        join(consumer)
    assert mailbox.snapshot().waiting_consumers == 0


def test_spurious_notification_rechecks_predicate(monkeypatch) -> None:
    mailbox = LatestFrameMailbox()
    first_wait = Event()
    second_wait = Event()
    real_wait = mailbox._condition.wait
    waits = 0

    def observe_wait(timeout=None):
        nonlocal waits
        waits += 1
        if waits == 1:
            first_wait.set()
        if waits == 2:
            second_wait.set()
        return real_wait(timeout)

    monkeypatch.setattr(mailbox._condition, "wait", observe_wait)
    result = []
    consumer = Thread(target=capture_get, args=(mailbox, result), daemon=False)
    consumer.start()
    try:
        assert first_wait.wait(GUARD_S)
        # Use the lock to notify only after the observed consumer wait begins.
        # wait_until_waiting also waits on this condition, so do not use it here.
        with mailbox._condition:
            assert mailbox._waiting == 1
            mailbox._condition.notify_all()
        assert second_wait.wait(GUARD_S)
        frame = Frame(0, 0, 0)
        mailbox.submit(frame)
        join(consumer)
        assert result == [frame]
    finally:
        mailbox.close()
        join(consumer)


def test_submit_and_close_have_linearizable_accounting_across_races() -> None:
    for _ in range(50):
        mailbox = LatestFrameMailbox()
        barrier = Barrier(2, timeout=GUARD_S)
        outcome = []

        def publish(channel, rendezvous, observations) -> None:
            try:
                rendezvous.wait()
                channel.submit(Frame(0, 0, 0))
                observations.append("accepted")
            except MailboxClosed:
                observations.append("closed")
            except BaseException as error:
                observations.append(error)

        producer = Thread(
            target=publish, args=(mailbox, barrier, outcome), daemon=False
        )
        producer.start()
        try:
            barrier.wait()
            mailbox.close()
            join(producer)
            assert outcome in (["accepted"], ["closed"])
            if outcome == ["accepted"]:
                assert mailbox.get().frame_id == "epoch-0/frame-0"
            with pytest.raises(MailboxClosed):
                mailbox.get()
            state = mailbox.snapshot()
            assert state.accepted == state.delivered == (outcome == ["accepted"])
            assert state.pending == state.replaced == 0
        finally:
            mailbox.close()
            barrier.abort()
            join(producer)


def test_close_and_retrieval_race_drains_exactly_once() -> None:
    for _ in range(50):
        mailbox = LatestFrameMailbox()
        frame = Frame(0, 0, 0)
        mailbox.submit(frame)
        barrier = Barrier(2, timeout=GUARD_S)
        result = []

        def consume(channel, rendezvous, observations) -> None:
            try:
                rendezvous.wait()
                capture_get(channel, observations)
            except BaseException as error:
                observations.append(error)

        consumer = Thread(target=consume, args=(mailbox, barrier, result), daemon=False)
        consumer.start()
        try:
            barrier.wait()
            mailbox.close()
            join(consumer)
            assert result == [frame]
            with pytest.raises(MailboxClosed):
                mailbox.get()
            assert mailbox.snapshot().delivered == 1
        finally:
            mailbox.close()
            barrier.abort()
            join(consumer)


@pytest.mark.parametrize(
    "timeout", [-1, float("nan"), float("inf"), True, "1", TIMEOUT_MAX + 1, 10**1000]
)
def test_invalid_timeouts_fail_before_waiting(timeout) -> None:
    mailbox = LatestFrameMailbox()
    with pytest.raises(ValueError):
        mailbox.get(timeout)
    with pytest.raises(ValueError):
        mailbox.wait_until_waiting(timeout)
    assert mailbox.snapshot().waiting_consumers == 0
