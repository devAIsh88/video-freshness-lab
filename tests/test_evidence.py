from dataclasses import FrozenInstanceError, replace
from fractions import Fraction

import pytest

from video_freshness_lab.evidence import FrameEvidence, Timestamp, diagnose
from video_freshness_lab.threaded_sessions import SessionPipeline

NS = Fraction(1, 1_000_000_000)


def stamp(ticks=10, **changes):
    return replace(
        Timestamp(ticks, NS, "fixture-clock", "controlled source clock", "verified"),
        **changes,
    )


def frame(**changes):
    return replace(
        FrameEvidence(
            "synthetic-source",
            0,
            1,
            provenance="fixture source sequence",
            sequence_kind="source_order",
            arrival_ns=20,
            arrival_domain="fixture-clock",
            pts=stamp(),
            capture=stamp(),
        ),
        **changes,
    )


def evaluate(evidence=None, **changes):
    options = dict(
        current_source="synthetic-source",
        current_epoch=0,
        now_ns=30,
        clock_domain="fixture-clock",
        max_age_ns=20,
    )
    options.update(changes)
    return diagnose(frame() if evidence is None else evidence, **options)


def test_valid_order_exact_rescaling_and_age_budget_boundary():
    prior = frame(sequence=0, pts=stamp(5), arrival_ns=15)
    current = frame(pts=stamp(1, time_base=NS * 10))
    result = evaluate(current, previous=prior)
    assert result.session == "current"
    assert result.age_status == "fresh"
    assert result.age_ns == 20
    assert result.issues == ()
    expired = evaluate(current, now_ns=31)
    assert expired.age_status == "stale"
    assert expired.age_ns == 21
    assert expired.issues == ("age_budget_exceeded",)


def test_missing_timestamps_do_not_become_zero_latency():
    result = evaluate(frame(pts=None, capture=None))
    assert result.session == "current"
    assert result.age_status == "unknown"
    assert result.age_ns is None
    assert set(result.issues) == {
        "missing_pts",
        "missing_capture",
        "insufficient_age_evidence",
    }


def test_local_arrival_age_is_independent_of_capture_freshness():
    evidence = frame(capture=None, pts=stamp(trust="reported"))
    assert evaluate(evidence).age_status == "unknown"
    recent = evaluate(evidence, age_reference="arrival")
    assert (recent.age_status, recent.age_ns) == ("fresh", 10)
    old = evaluate(evidence, age_reference="arrival", now_ns=41)
    assert (old.age_status, old.age_ns) == ("stale", 21)
    assert old.evidence is evidence


def test_identical_synthetic_pixels_do_not_prove_freeze_or_new_capture():
    # These symbolic payloads model identical content; no image/decoder is used.
    observations = [
        ("same-pattern", frame(capture=None)),
        ("same-pattern", frame(sequence=2, arrival_ns=25, capture=None)),
    ]
    assert observations[0][0] == observations[1][0]
    first = evaluate(observations[0][1], age_reference="arrival")
    second = evaluate(
        observations[1][1], age_reference="arrival", previous=observations[0][1]
    )
    assert (first.age_ns, second.age_ns) == (10, 5)
    assert "frame_identity_not_advancing" not in second.issues
    assert evaluate(observations[1][1]).age_status == "unknown"


@pytest.mark.parametrize("base", [None, Fraction(0), Fraction(-1, 1000)])
def test_missing_or_invalid_time_base_remains_inconclusive(base):
    evidence = frame(pts=stamp(time_base=base), capture=stamp(time_base=base))
    result = evaluate(evidence)
    kind = "missing" if base is None else "invalid"
    assert f"{kind}_pts_time_base" in result.issues
    assert f"{kind}_capture_time_base" in result.issues
    assert result.age_status == "unknown"
    assert result.age_ns is None


@pytest.mark.parametrize(
    "changes", [{"trust": "reported"}, {"provenance": None}, {"domain": "other-clock"}]
)
def test_unsubstantiated_or_unmapped_capture_time_cannot_establish_age(changes):
    result = evaluate(frame(capture=stamp(**changes)))
    assert result.age_status == "unknown"
    assert result.age_ns is None
    assert "insufficient_age_evidence" in result.issues


def test_missing_provenance_and_unknown_order_are_reported_separately_from_age():
    result = evaluate(frame(source_id=None, provenance=None, sequence_kind="unknown"))
    assert result.session == "unknown"
    assert (
        result.age_status == "fresh"
    )  # The controlled capture reference still exists.
    assert set(result.issues) == {
        "missing_session_provenance",
        "missing_provenance",
        "unknown_frame_order",
    }


@pytest.mark.parametrize("changes", [{"epoch": 1}, {"source_id": "other-source"}])
def test_session_mismatch_does_not_hide_measurable_age(changes):
    result = evaluate(frame(**changes), now_ns=100)
    assert result.session == "obsolete_session"
    assert result.age_status == "stale"
    assert {"session_mismatch", "age_budget_exceeded"} <= set(result.issues)


def test_reconnect_reset_is_compared_only_inside_a_known_session():
    previous = frame(sequence=10, pts=stamp(1000))
    reset = frame(epoch=1, sequence=0, pts=stamp(0))
    result = evaluate(reset, current_epoch=1, previous=previous)
    assert result.session == "current"
    assert "pts_regression" not in result.issues
    assert "frame_identity_not_advancing" not in result.issues
    unannounced = evaluate(replace(reset, epoch=0), previous=previous)
    assert {"pts_regression", "frame_identity_not_advancing"} <= set(unannounced.issues)


def test_timestamp_gap_and_regression_have_declared_meaning():
    previous = frame(sequence=0, pts=stamp(0), arrival_ns=25)
    result = evaluate(frame(pts=stamp(50)), previous=previous, max_pts_gap_ns=49)
    assert {"pts_discontinuity", "arrival_regression"} <= set(result.issues)
    assert (
        "pts_discontinuity"
        not in evaluate(
            frame(pts=stamp(50)), previous=previous, max_pts_gap_ns=50
        ).issues
    )
    assert "pts_discontinuity" not in evaluate(previous=previous).issues
    # Signed media timestamps are legitimate; repeated PTS alone is not a defect.
    assert "pts_regression" in evaluate(frame(pts=stamp(-1)), previous=previous).issues
    assert (
        "pts_regression" not in evaluate(frame(pts=stamp(0)), previous=previous).issues
    )


def test_incomparable_timelines_and_identity_kinds_are_not_subtracted():
    previous = frame(sequence=9)
    current = frame(sequence_kind="local_delivery", pts=stamp(0, domain="new-segment"))
    result = evaluate(current, previous=previous)
    assert "incomparable_pts" in result.issues
    assert "pts_regression" not in result.issues
    assert "frame_identity_not_advancing" not in result.issues


def test_future_and_causally_impossible_timestamps_are_unknown():
    future = evaluate(frame(capture=stamp(31)))
    assert future.age_status == "unknown"
    assert future.age_ns is None
    assert "future_age_reference" in future.issues
    impossible = evaluate(frame(capture=stamp(21)))
    assert impossible.age_status == "unknown"
    assert "capture_after_arrival" in impossible.issues
    future_arrival = evaluate(frame(arrival_ns=31))
    assert future_arrival.age_status == "unknown"
    assert future_arrival.age_ns is None
    assert "arrival_after_evaluation" in future_arrival.issues
    missing = evaluate(frame(arrival_ns=None), age_reference="arrival")
    assert missing.age_ns is None
    assert missing.age_status == "unknown"


def test_obsolete_result_keeps_original_evidence_after_session_transition():
    pipeline = SessionPipeline()
    original = pipeline.produce(1)
    evidence = frame(
        epoch=original.session_id,
        sequence=original.sequence,
        capture=None,
        admission="accepted",
        admission_reason="source admitted",
    )
    assert pipeline.acquire() is original
    pipeline.transition()
    pipeline.close()
    completion = pipeline.complete(original, 100)
    assert completion.outcome == "obsolete"
    result = evaluate(evidence, current_epoch=pipeline.snapshot().epoch)
    assert result.session == "obsolete_session"
    assert result.age_status == "unknown"
    assert result.evidence.admission == "accepted"  # Historical fact, not a verdict.
    rejected = replace(
        evidence, admission="rejected", admission_reason="obsolete result"
    )
    assert evaluate(rejected, current_epoch=1).session == "obsolete_session"
    assert pipeline.snapshot().outputs == ()


def test_structural_validation_and_immutable_metadata():
    evidence = frame(decoder_metadata=(("decoder", "synthetic"),))
    with pytest.raises(FrozenInstanceError):
        evidence.epoch = 9
    for changes in (
        {"epoch": True},
        {"sequence": -1},
        {"source_id": ""},
        {"decoder_metadata": []},
        {"admission": "maybe"},
        {"sequence_kind": "maybe"},
        {"pts": 0},
    ):
        with pytest.raises((ValueError, TypeError)):
            frame(**changes)
    for changes in ({"ticks": True}, {"time_base": 0.1}, {"trust": "maybe"}):
        with pytest.raises((ValueError, TypeError)):
            stamp(**changes)
    for changes in (
        {"now_ns": -1},
        {"max_age_ns": True},
        {"clock_domain": ""},
        {"age_reference": "pts"},
        {"max_pts_gap_ns": -1},
    ):
        with pytest.raises(ValueError):
            evaluate(**changes)
