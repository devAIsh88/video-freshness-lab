from dataclasses import replace
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from video_freshness_lab.evidence import FrameEvidence
from video_freshness_lab.gstreamer_contract import (
    ExperimentConfig,
    PublicationLedger,
    accounting,
    associate,
    encode_id,
)
from video_freshness_lab.gstreamer_experiment import run_isolated


def test_configuration_rejects_unsupported_or_unbounded_cases():
    config = ExperimentConfig("fifo", False, "balanced")
    for changes in (
        {"policy": "other"},
        {"workload": "infinite"},
        {"session_filter": 1},
        {"guard_s": 0},
        {"guard_s": float("nan")},
        {"guard_s": 11},
    ):
        with pytest.raises(ValueError):
            replace(config, **changes)


def test_wire_identity_uses_explicit_registry_not_timestamps_or_position():
    original = FrameEvidence("synthetic-source", 4, 0)
    registry = {17: original}
    token, evidence = associate(encode_id(17), registry)
    assert token == 17 and evidence is original
    for payload in (b"", b"wrong" + encode_id(17)[5:], encode_id(18)):
        with pytest.raises(ValueError):
            associate(payload, registry)
    with pytest.raises(ValueError):
        encode_id(True)


def test_native_replacements_are_distinct_from_application_rejections():
    values = accounting(
        submitted=4, received=3, native_drops=1, rejected=1, published=2, unpulled=0
    )
    assert values["native_drops"] + values["rejected"] == 2
    with pytest.raises(ValueError, match="native accounting"):
        accounting(**(values | {"native_drops": 2}))
    with pytest.raises(ValueError, match="application accounting"):
        accounting(**(values | {"rejected": 0}))
    assert (
        accounting(
            submitted=2, received=0, native_drops=0, rejected=0, published=0, unpulled=2
        )["unpulled"]
        == 2
    )


def test_filter_changes_final_admission_not_original_evidence():
    evidence = FrameEvidence("synthetic-source", 0, 1, admission="accepted")
    for filtered in (False, True):
        ledger = PublicationLedger(filtered)
        before = ledger.complete(0, evidence, 1)
        ledger.transition()
        after = ledger.complete(1, evidence, 2)
        assert before["published"] and not before["obsolete"]
        assert after["obsolete"] and after["published"] is (not filtered)
        assert ledger.events[1] == {"transition": 1}
        assert evidence.admission == "accepted" and evidence.epoch == 0
        after["published"] = not after["published"]
        snapshot = ledger.events
        snapshot[2]["published"] = not snapshot[2]["published"]
        assert ledger.events[2]["published"] is (not filtered)


def test_supervisor_reports_native_process_failure_without_retry(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(args)
        return CompletedProcess(args, 1, "", "synthetic failure")

    monkeypatch.setattr("video_freshness_lab.gstreamer_experiment.subprocess.run", fail)
    result = run_isolated(ExperimentConfig("leaky", False, "slow"))
    assert result["status"] == "error"
    assert result["stderr"] == "synthetic failure"
    assert len(calls) == 1


def test_supervisor_bounds_native_hang(monkeypatch):
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 15
        raise TimeoutExpired("synthetic child", 15)

    monkeypatch.setattr(
        "video_freshness_lab.gstreamer_experiment.subprocess.run", timeout
    )
    result = run_isolated(ExperimentConfig("fifo", False, "shutdown"))
    assert result["status"] == "error"
    assert result["error"] == "subprocess watchdog expired"
