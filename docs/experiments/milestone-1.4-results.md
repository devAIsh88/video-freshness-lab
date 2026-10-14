# Milestone 1.4: thread-safe handoff and clean shutdown

## Scope and configuration

This milestone follows the local PRDs' threaded learning-demo and clean-shutdown
requirements. Both original PRDs remain unchanged, untracked, and excluded from
publication. The implementation uses standard-library threading and the existing
immutable synthetic `Frame`; it leaves the virtual simulation engine unchanged.
See the [mailbox architecture](../architecture/threaded-mailbox.md) for admission,
ownership, counters, failure handling, and explicit drain-on-close semantics.

Environment: Fedora Linux 44, Python 3.12.15, pytest 8.4.2, Ruff 0.14.0, existing
editable installation. No runtime dependency was added. CI retains Python 3.11
and 3.12 lint/format/test jobs; remote results are reported with milestone delivery.

## Reproduction and observations

Run from the repository root, without camera access or network:

```sh
.venv/bin/python -m video_freshness_lab.threaded_demo --mode normal --items 10
.venv/bin/python -m video_freshness_lab.threaded_demo --mode slow --items 10
.venv/bin/python -m video_freshness_lab.threaded_demo --mode idle
.venv/bin/python -m video_freshness_lab.threaded_demo --mode slow --items 10 --json
```

Actual results from the CLI and corresponding tests:

| Mode | Produced / accepted | Delivered | Replaced | Delivered sequences |
| --- | --- | --- | --- | --- |
| Normal, 10 | 10 / 10 | 10 | 0 | 0 through 9 |
| Slow, 10 | 10 / 10 | 2 | 8 | 0, 9 |
| Idle, 0 | 0 / 0 | 0 | 0 | None |

All three report zero rejected submissions, a closed empty mailbox with zero
waiting consumers, both worker-finished flags true, and terminated threads.
Normal uses retrieval acknowledgements; slow holds the first in-progress frame
until production ends. Thus the counts are outcomes of explicit synchronization,
not measurements of an unconstrained producer rate or scheduler performance.
Production timestamps are elapsed monotonic milliseconds and need not match
across runs.

The shutdown-with-pending test coordinates a callback and a second accepted
frame, then requests stop. It verifies both accepted frames drain without
replacement. Empty-consumer shutdown verifies notification and termination.
A forced stop-before-submission race separately observes one constructed frame,
one rejected submission, and zero accepted frames. Rejections are not drops of
accepted data.

## Validation

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

Local validation: **217 tests pass**, including all **170 existing tests** and
**47 new test cases**. Ruff lint and formatting checks pass; pip reports no broken
requirements; working/staged whitespace checks pass. Editable package imports and
installed module CLI execution pass. Existing CI configuration remains unchanged.

New tests verify original frame identity, immutable metadata/snapshots, monotonic
admission, exact replacement accounting, timeout boundaries, no duplicate delivery,
post-close behavior, idempotent close, spurious wakeup handling, blocked-consumer
notification, producer stop, pending drain, and startup/worker failure reporting.
Two barrier-coordinated races repeat 50 times each (submit versus close, retrieval
versus close). A lifecycle test runs 100 fresh normal, 100 slow, and 100 idle demos,
joining all 600 workers. An autouse guard checks no additional threads remain after
each test. All coordination uses explicit primitives; no arbitrary sleeps are
used as correctness assumptions.

An intentionally uncooperative callback test confirms a bounded join reports the
live consumer instead of concealing it with daemonization. Test cleanup explicitly
releases and joins that worker. A parked-consumer fault injection leaves a pending
frame for owner drainage; it is not a successful built-in demo configuration.

## Security and limitations

Only synthetic numbered metadata is used. No camera connections, real media,
credentials, private connection URLs, new dependencies, deployment, publishing,
or license changes are introduced. Original PRDs and local environments remain
outside Git. Licensing remains pending; synchronization is to the private repository
only. Commit, remote verification, and CI status are recorded in the delivery report.

These observations establish behavior of this mailbox and coordinated learning
demo under tested schedules. They do not establish complete race freedom or
validate real RTSP reconnection behavior. SPSC ownership and cooperative callbacks
remain explicit constraints. Drain-on-close favors completion of an accepted item;
it does not invalidate an in-progress old-session result or enforce freshness.
Transport lineage, camera timestamps, real image memory ownership, real-library
buffering, and external session identification remain unresolved research work.

A subsequent owner-approved learning milestone could test synthetic application
output provenance across threaded session changes, including invalidation of an
in-progress obsolete result. Real-library evaluation still requires the PRD's
evidence gates; no real RTSP integration starts here.
