# Milestone 1.5: obsolete-result rejection across threaded sessions

## Method and reproducibility

This experiment follows the local PRDs' session/evidence and final-output rules
under the explicit owner authorization for Milestone 1.5. Original PRDs remain
unchanged and untracked. Results below are synthetic application observations,
not external RTSP/library findings. See the [session architecture](../architecture/threaded-session-boundaries.md).

Fedora Linux 44, Python 3.12.15, pytest 8.4.2, Ruff 0.14.0, existing editable
installation; no dependencies added. The original simulator and threaded mailbox
are unchanged, including drain-on-close. The unchanged CI matrix tests Ubuntu
Python 3.11 and 3.12; remote delivery/CI results follow in the final report.

```sh
.venv/bin/python -m pytest tests/test_threaded_sessions.py -v
.venv/bin/python -m pytest tests/test_threaded_sessions.py -k obsolete_active -v
.venv/bin/python -m pytest tests/test_threaded_sessions.py -k hundred -v
```

The critical script is: produce epoch-0 sequence-0, acquire it, pause processing
on an event, activate the next epoch, produce its sequence-0, signal production,
then release processing. The test owner observes the new epoch and zero completed
outputs before releasing the consumer. Source closure permits drainage. With
three transitions, epochs 1 and 2 are replaced while waiting, and epoch 3 survives.
Frames use explicit integer millisecond stamps (1 for the original, 2 for later
productions); these are scenario metadata, not measured processing duration.

## Actual outcomes

The table records final application state before test teardown shutdown. Produced
and accepted are identical in this API. All listed workloads drain completely.

| Scenario | Produced | Replaced | Acquired / processed | Obsolete | Published | Shutdown discarded |
| --- | --- | --- | --- | --- | --- | --- |
| Normal, one epoch, two items | 2 | 0 | 2 / 2 | 0 | 2 | 0 |
| Transition with old waiting frame, no replacement | 1 | 0 | 1 / 1 | 1 | 0 | 0 |
| Transition with new waiting replacement | 2 | 1 | 1 / 1 | 0 | 1 | 0 |
| Active old frame, one transition and newer production | 2 | 0 | 2 / 2 | 1 | 1 | 0 |
| Active old frame, three consecutive transitions | 4 | 2 | 2 / 2 | 1 | 1 | 0 |
| Active old frame, ten consecutive transitions | 11 | 9 | 2 / 2 | 1 | 1 | 0 |
| Shutdown with active frame | 1 | 0 | 1 / 1 | 0 | 0 | 1 |
| Shutdown with active and pending frames | 2 | 0 | 2 / 2 | 0 | 0 | 2 |

The old result finishes with value 100 in the paused-processing scenarios, but
never appears in `outputs`. Its completion retains epoch-0 provenance and records
the current newer epoch with an `obsolete` outcome. The trace verifies that newer
production precedes this rejected completion. The sole output belongs to the
latest epoch. A transition without newer production also suppresses the old
active result: validity depends on the boundary, not a newer frame's arrival.

Source close alone permits a current-epoch pending result to publish. Application
shutdown instead disables output admission before waking the processing callback;
active and pending frames are drained and successful results classified as
shutdown discards. Neither operation mutates frame provenance.

## Races and failures

Close versus transition is tested for 50 barrier-coordinated races, with the
consumer started afterward. Every run retains the pending epoch-0 item in a
closed mailbox, advances to epoch 1 without reopening input, and rejects the
retained result on final completion.

Publication versus transition is also raced 50 times. Either publication precedes
activation of the new epoch (valid historical output), or activation precedes
completion (obsolete rejection). Tests verify only legal linearizations; they do
not promise a winning thread or fabricate a repeatable count for an unordered
race. Two ordered controls separately verify both outcomes. Validation and ledger
insertion share a lock, with no external callback between them.

Producer failure after the transition disables output admission and signals stop;
the active consumer completes and its result is shutdown-discarded. Consumer
failure after the transition counts one processing failure, zero successful
completions, and zero outputs. The original exception and worker role reach the
test owner. A separate failed-consumer scenario preserves one pending item for
explicit owner drainage; no accepted item disappears from accounting. Invalid
processing return data is a failure, not a successful obsolete rejection.

## Validation

The new suite has **23 passing test cases**. Its 100 fresh critical-boundary runs
each perform three transitions, suppress the original result, publish the newest,
and join both non-daemon workers. There were no failed repetitions in this local
run. This is finite controlled evidence, not proof of general race freedom or
the PRD's later external integration flake-rate gate.

The full suite passes **240 tests**, preserving all **217 previous tests**.
Ruff lint/format, dependency integrity, editable-package import, existing module
CLI tests, and working/staged whitespace checks pass. Test cleanup uses bounded
joins and the existing thread-leak guard. Events and barriers establish ordering;
timeouts guard against hangs, and no arbitrary sleeps are used.

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

## Security, limitations, and remaining gates

Only synthetic numbered evidence and integer results are used. No secrets,
camera connections, media, video dependencies, deployment, paid services, or
license changes are introduced. Original PRDs and environments remain outside
Git. Licensing remains pending and synchronization is private only.

Publication here means admission to a locked in-memory output ledger. A later
network/UI/device sink would require its own ordering/transaction contract;
checking an epoch then sending outside the lock would reopen the race. Logical
epoch transitions are controller-defined, not real RTSP source identity detection.
There is no age-based filtering, disconnected-epoch gap, forced callback
termination, multi-camera support, or image-memory validation. Windows remains
an unverified portability target.

Remaining PRD gates include synthetic stamped-image lineage, real-library/source
selection and equivalent contract evaluation, documented external flake rates,
third-party audit, adapter-size/value evidence, maintainer acknowledgment, adoption
interest, and the package/upstream/recipe/stop decision. Licensing and public
publication also remain owner decisions. Synthetic success satisfies none of the
external evidence or market-gap claims.

Recommended next authorized learning milestone: review and consolidate a small
evidence-to-output adapter and actionable session/order failures before adding
image or transport dependencies. No later milestone is implemented here.
