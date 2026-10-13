import pytest

from video_freshness_lab.buffers import FIFO, LatestFrame
from video_freshness_lab.model import Frame


def test_fifo_preserves_arrival_order() -> None:
    buffer = FIFO()
    frames = [Frame(0, i, i) for i in [2, 0, 1]]
    for frame in frames:
        assert buffer.push(frame).admitted
    assert len(buffer) == 3
    assert [buffer.pop() for _ in frames] == frames
    with pytest.raises(IndexError):
        buffer.pop()


@pytest.mark.parametrize(
    ("policy", "expected", "dropped", "admitted"),
    [("drop_newest", [0, 1], 2, False), ("drop_oldest", [1, 2], 0, True)],
)
def test_fifo_overflow(policy, expected, dropped, admitted) -> None:
    buffer = FIFO(2, policy)
    frames = [Frame(0, i, i) for i in range(3)]
    buffer.push(frames[0])
    buffer.push(frames[1])
    admission = buffer.push(frames[2])
    assert admission.admitted is admitted
    assert admission.dropped == (frames[dropped],)
    assert admission.reason == f"overflow_{policy}"
    assert len(buffer) == 2
    assert [buffer.pop().sequence for _ in range(2)] == expected


def test_latest_replaces_waiting_frame_only() -> None:
    buffer = LatestFrame()
    active = Frame(0, 0, 0)
    buffer.push(active)
    assert buffer.pop() == active
    waiting = Frame(0, 1, 10)
    newest = Frame(0, 2, 20)
    assert buffer.push(waiting).dropped == ()
    admission = buffer.push(newest)
    assert admission.admitted and admission.dropped == (waiting,)
    assert admission.reason == "replaced" and len(buffer) == 1
    assert active.sequence == 0
    assert buffer.pop() == newest


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_invalid_capacity(capacity) -> None:
    with pytest.raises(ValueError):
        FIFO(capacity)
