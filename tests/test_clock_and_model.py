from dataclasses import FrozenInstanceError

import pytest

from video_freshness_lab.clock import VirtualClock
from video_freshness_lab.model import Frame


def test_frame_identity_and_immutability() -> None:
    frame = Frame(2, 7, 100)
    assert frame.frame_id == "epoch-2/frame-7"
    assert Frame(3, 7, 100).frame_id != frame.frame_id
    with pytest.raises(FrozenInstanceError):
        frame.sequence = 8


@pytest.mark.parametrize(
    "values", [(-1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1.5), (True, 0, 0)]
)
def test_invalid_frame(values) -> None:
    with pytest.raises(ValueError):
        Frame(*values)


def test_clock_timestamp_priority_and_insertion_order() -> None:
    clock = VirtualClock()
    seen = []
    clock.schedule(5, lambda: seen.append("later"))
    clock.schedule(2, lambda: seen.append("priority-two"), priority=2)
    clock.schedule(2, lambda: seen.append("first-one"), priority=1)
    clock.schedule(2, lambda: seen.append("second-one"), priority=1)
    clock.run_until(2)
    assert seen == ["first-one", "second-one", "priority-two"]
    assert clock.now_ms == 2 and clock.pending_count == 1
    clock.run()
    assert seen[-1] == "later" and clock.now_ms == 5
    clock.run_until(10)
    assert clock.now_ms == 10


def test_clock_can_schedule_from_callback() -> None:
    clock = VirtualClock()
    seen = []

    def callback() -> None:
        seen.append(clock.now_ms)
        clock.schedule(clock.now_ms, lambda: seen.append(clock.now_ms), priority=1)

    clock.schedule(3, callback)
    clock.run()
    assert seen == [3, 3] and clock.pending_count == 0


def test_clock_rejects_backwards_time_and_nested_execution() -> None:
    clock = VirtualClock()
    clock.run_until(5)
    with pytest.raises(ValueError):
        clock.schedule(4, lambda: None)
    with pytest.raises(ValueError):
        clock.run_until(4)
    with pytest.raises(ValueError):
        clock.schedule(6.5, lambda: None)
    with pytest.raises(ValueError):
        clock.schedule(6, None)
    clock.schedule(6, clock.run)
    with pytest.raises(ValueError, match="nested"):
        clock.run()
    # Exceptions release the execution guard.
    clock.run_until(7)
    assert clock.now_ms == 7
