"""Source marker format stays testable without any optional media dependency."""

import struct
import zlib
from dataclasses import FrozenInstanceError

import pytest

from video_freshness_lab.stamped_images import Marker


@pytest.mark.parametrize(
    "values", [(0, 0, 0), (7, 3, 99), (2**32 - 1, 2**32 - 1, 2**32 - 1)]
)
def test_source_epoch_sequence_marker_is_exact_and_immutable(values):
    marker = Marker(*values)
    assert Marker.from_wire(marker.wire()) == marker
    with pytest.raises(FrozenInstanceError):
        marker.epoch = 1


@pytest.mark.parametrize("values", [(-1, 0, 0), (0, True, 0), (0, 0, 2**32)])
def test_invalid_source_marker_never_wraps_or_aliases(values):
    with pytest.raises(ValueError):
        Marker(*values)


def test_corruption_and_foreign_format_do_not_become_a_delivery_identifier():
    original = Marker(7, 0, 17).wire()
    changed = original[:5] + bytes([original[5] ^ 1]) + original[6:]
    assert Marker.from_wire(changed) is None
    assert Marker.from_wire(original[:-1]) is None
    body = b"OTHR" + original[4:-4]
    assert Marker.from_wire(body + struct.pack("!I", zlib.crc32(body))) is None
