"""RTSP sidecar semantics, without GI, sockets, sleeps or native dependencies."""

import pytest

from video_freshness_lab import rtsp_experiment
from video_freshness_lab.evidence import diagnose
from video_freshness_lab.gstreamer_contract import PublicationLedger
from video_freshness_lab.rtsp_contract import RtspConfig, receipt_evidence


@pytest.mark.parametrize(
    "args", [("unknown",), ("normal", "unknown"), ("normal", "fifo", 1)]
)
def test_invalid_experiment_configuration(args):
    with pytest.raises(ValueError):
        RtspConfig(*args)


@pytest.mark.parametrize("filtered", [False, True])
def test_held_receipt_keeps_its_epoch_across_output_transition(filtered):
    old = receipt_evidence(generation=0, epoch=0, ordinal=7, receipt_ns=10, pts=0)
    ledger = PublicationLedger(filtered)
    ledger.transition()
    new = receipt_evidence(generation=1, epoch=1, ordinal=0, receipt_ns=20, pts=0)
    decision = ledger.complete(7, old, 30)
    assert decision["obsolete"]
    assert decision["published"] is (not filtered)
    assert ledger.complete(8, new, 31)["published"]
    assert old.epoch == 0
    assert old.decoder_metadata == (("connection_generation", "0"),)
    assert new.pts.domain != old.pts.domain


def test_delivery_identity_and_decoder_pts_do_not_prove_capture_freshness():
    item = receipt_evidence(generation=0, epoch=0, ordinal=3, receipt_ns=10, pts=25)
    diagnostic = diagnose(
        item,
        current_source="loopback-fixture",
        current_epoch=0,
        now_ns=20,
        clock_domain="rtsp-client-monotonic",
        max_age_ns=100,
    )
    assert diagnostic.age_status == "unknown"
    assert diagnostic.age_ns is None
    assert item.capture is None
    assert item.sequence_kind == "local_delivery"
    assert item.pts.trust == "reported"
    assert item.pts.nanoseconds() == 25


def test_missing_decoder_pts_stays_missing():
    item = receipt_evidence(generation=0, epoch=0, ordinal=0, receipt_ns=0, pts=None)
    assert item.pts is None


@pytest.mark.parametrize("generation", [-1, True])
def test_invalid_connection_generation(generation):
    with pytest.raises((ValueError, TypeError)):
        receipt_evidence(
            generation=generation, epoch=0, ordinal=0, receipt_ns=0, pts=None
        )


def test_cli_supervisor_launches_importable_module(monkeypatch):
    """Running as python -m must not propagate __main__ to child module lookup."""
    launches = []

    class Child:
        returncode = 0

        def __init__(self, args, **kwargs):
            launches.append(args)

        def communicate(self, **kwargs):
            return '{"status": "ok"}', ""

    monkeypatch.setattr(rtsp_experiment, "__name__", "__main__")
    monkeypatch.setattr(rtsp_experiment.subprocess, "Popen", Child)
    assert rtsp_experiment.run_isolated(RtspConfig("normal"))["status"] == "ok"
    assert launches[0][1:3] == ["-m", "video_freshness_lab.rtsp_experiment"]
