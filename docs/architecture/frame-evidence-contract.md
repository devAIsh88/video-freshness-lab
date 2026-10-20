# Frame evidence contract

Milestone 1.6 adds immutable observations and a pure diagnostic function in
`video_freshness_lab.evidence`. This is a research contract, not a transport
adapter or output admission service. It makes explicit the uncertainty that the
numbered-item experiments could avoid by owning the source and clock. The owner
authorized this narrow contract/research milestone beyond 1.5; the original PRDs,
their differences in [foundation.md](foundation.md), and all external validation
and adoption gates remain intact.

## Observation schema

| Field | Meaning and availability | Limit |
| --- | --- | --- |
| `source_id` | Local opaque alias assigned by the application; `None` if unknown | Never a URL, credential, or claim of authenticated physical camera identity |
| `epoch` | Nonnegative controller-owned logical generation; `None` if unknown | Never infer a physical restart solely from a reconnect, PTS reset, or connection success |
| `sequence` | Nonnegative per-source/per-epoch ordinal, or `None` | Meaning depends on `sequence_kind` and `provenance` |
| `sequence_kind` | `source_order`, `local_delivery`, or `unknown` | A delivery counter proves local order only; it cannot detect repeated source images |
| `provenance` | Explanation of identity assignment, or `None` | Caller assertion, not cryptographic proof |
| `arrival_ns` | Locally observed monotonic time at the declared application receipt boundary, or `None` | Does not include unknown upstream buffering or equal physical capture time |
| `arrival_domain` | Opaque identifier for the monotonic clock origin/lifetime, or `None` | A clock name shared by two hosts does not establish synchronization |
| `pts` | Optional `Timestamp` copied from a decoder/source presentation field | Presentation schedule, not physical capture time |
| `capture` | Optional `Timestamp` whose exposure/capture meaning has supporting evidence | Omit when only PTS, decoder completion, or local arrival is known |
| `decoder_metadata` | Immutable tuple of string pairs, empty if unavailable | Sanitized descriptive metadata only; uninterpreted and never used as an implicit trust signal |
| `admission`, `admission_reason` | Observed acceptance/rejection at this boundary, or `unknown` | Historical observation, not a diagnostic decision or proof of final delivery |

`Timestamp` stores signed integer `ticks`, optional exact `Fraction` seconds per
tick, a domain, provenance, and trust. Signed media PTS may be legitimate. Zero
is a real tick, never a missing-value sentinel. Missing stamps are `None`.
Missing time bases are `None`; zero or negative rational bases are retained for
diagnostics. Floats and mutable nested metadata are rejected structurally.
A decoder rational with zero denominator cannot be represented by `Fraction`:
an adapter must retain a sanitized raw description in decoder metadata and mark
the interpreted base unavailable. It must not substitute FPS or seconds by guess.

Trust is `unknown` (unsubstantiated), `reported` (identified provider field), or
`verified` (meaning substantiated for this experiment). Verified is an assertion
requiring a recorded method, not library reputation or authentication. A future
adapter must describe whether a PTS was source-provided, generated, interpolated,
or rescaled. Merely copying a decoder field warrants at most `reported`.

A timestamp domain identifies both an origin and a continuous timeline segment.
Source PTS and local monotonic time normally occupy different domains. Their
numeric units can be converted without their origins becoming comparable.
Capture age is permitted only when verified capture semantics and an exact
mapping into the evaluation clock domain have been substantiated. Approximate
NTP mappings, clock uncertainty, drift, and exposure intervals need an explicit
bounded-error model in a later milestone; they cannot earn `verified` here.
The synthetic fixture's injected clock is the only verified capture reference
used in 1.6. There is no automatic clock mapping or discovery.

## Meaningful comparisons

| Comparison | Required evidence | What it establishes |
| --- | --- | --- |
| Identity progression | Same known source/epoch, same known sequence kind and identity provenance | Nonadvancing ordinal; source order only when source ordinals are established |
| PTS delta | Same known source/epoch, same known PTS domain and provenance, reported/verified stamps with positive exact bases | Media-time progression, regression, or a declared gap; not wall-time latency |
| Arrival order | Same known source/epoch and local arrival domain | Order of local receipt observations |
| `now - arrival` | Same local monotonic domain | Time since application receipt; excludes time before receipt |
| `now - capture` | Verified capture meaning, provenance, positive base, exact shared evaluation domain | Observable capture age within the experiment's assumptions |
| Session validity | Known expected source/epoch and observed source/epoch | Match or mismatch with the controller's current logical generation |

Different positive time bases can be rescaled exactly within a comparable domain.
No sequence or PTS subtraction occurs across epochs or sources. A reset in a new
epoch is not regression. A reset inside a declared continuous epoch is reported;
seek, edit, wrap, bad boundary inference, reordering, or genuine source behavior
remain possible explanations. A changed PTS domain reports `incomparable_pts`.
PTS equality alone is not treated as an error. Forward gaps require a caller's
explicit `max_pts_gap_ns`; no nominal frame rate or universal gap limit is assumed.

Same-session local delivery order does not prove capture ordering. A caller
passing predecessors must choose the intended observation order and account for
codec reordering. Comparison with one predecessor is not global deduplication,
source-head lag, or freeze detection. Identical content may be a static scene;
new arrival times do not prove new exposures.

## Diagnostic contract

`diagnose` receives one observation, expected source/epoch, explicit `now_ns` and
clock domain, an age budget/reference, and optional predecessor/PTS gap budget.
It reads no clocks, owns no mutable state, opens no transport, and creates no
threads. Callers retain the returned `Diagnostic` with the exact evidence object.

The diagnostic has two independent axes:

- `session`: `current`, `obsolete_session` (any known source/epoch mismatch), or
  `unknown` when either side lacks session provenance.
- `age_status`: `fresh`, `stale`, or `unknown`, always qualified by `age_reference`
  (`capture` by default, or explicitly `arrival`). Equality with the declared
  budget passes; strict excess is an observable violation.

Thus an obsolete result can have a measurable fresh age. A missing identity can
coexist with measurable age. `fresh` never means overall validity or acceptance;
consumers must inspect both axes and issues. The API deliberately has no binary
pass/fail or implicit publication action. An invalid PTS does not invalidate an
independently verified capture reference; each finding retains its own meaning.

`age_ns` is an exact rational or `None`. Missing/untrusted/mismatched capture
references yield `unknown`, never zero. Future references and capture times after
same-domain arrival are invalid/inconclusive. Issue codes report missing
provenance, unknown frame order, session mismatch, missing/invalid bases, absent
arrival references, nonadvancing identity, arrival/PTS regression, incomparable
PTS, declared discontinuity, insufficient age evidence, impossible time ordering,
and budget violation. See the focused tests for exact codes. No discontinuity
finding is labeled a decoder bug.

## Compatibility and boundaries

The original frozen `model.Frame`, simulator, mailbox, CLI, and
`SessionPipeline` remain unchanged. A sidecar can carry `Frame.session_id` as
epoch and `Frame.sequence` as source ordinal after supplying a local source alias
and identity method. `produced_at_ms` must not automatically become capture time
or arrival time: simulator production and threaded receipt are different events.
The compatibility fixture deliberately leaves capture unknown.

Acceptance at arrival and obsolete rejection at final completion are distinct
observations. Construct a new frozen sidecar for a new boundary rather than
mutating historical evidence. A real result should retain its original sidecar;
only the expected session context changes at evaluation. The 1.5 output ledger
still supplies the atomic publication example; this pure diagnostic does not
replace that lock or establish a transaction with an external sink.

The minimal value demonstrated here is preventing a recent-arrival timestamp
from becoming a false capture-freshness pass while retaining independent session
findings. A dataclass plus pytest recipe may be enough. No public schema stability,
standalone-package gap, external defect, adapter-size success, or adoption claim
is established. See the [library comparison](../research/existing-library-capability-matrix.md)
and [1.6 results](../experiments/milestone-1.6-results.md).
