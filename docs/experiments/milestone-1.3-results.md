# Milestone 1.3: synthetic interruption and session recovery

Status: local experimental evidence from the same numbered-item engine. These
measurements establish how the explicit model behaves, not how RTSP, FFmpeg,
OpenCV, GStreamer, or any real camera behaves. No external consumer was audited.
See [architecture and metric policies](../architecture/simulation.md).

## Reproducible configurations

Every preset uses 10 ms producer ticks, an 80 ms result-age budget, a 25 ms source
no-progress timeout, and retained waiting queues on disconnect. Source horizon
is 100 ms except repeated recovery (150 ms) and obsolete delivery (60 ms).
Consumer duration is 40 ms except normal/no-progress (10 ms) and slowdown
(starts at 10 ms, changes to 40 ms at time 20 ms).

| Preset | Control script, in milliseconds |
| --- | --- |
| normal | No controls |
| consumer-slowdown | Change subsequent processing duration at 20 |
| freeze | Freeze at 20, unfreeze at 60; epoch unchanged |
| disconnect | Disconnect at 25; no reconnect |
| reconnect | Disconnect at 25, reconnect at 55 |
| repeated-recovery | Disconnect/reconnect at 25/55 and 85/115 |
| no-progress | Freeze at 10, unfreeze at 90 |
| obsolete-delivery | Disconnect at 10, reconnect at 20; active old work survives |
| session-filter | Reconnect script with session filtering enabled |

```sh
.venv/bin/python -m video_freshness_lab --suite recovery
.venv/bin/python -m video_freshness_lab --suite recovery --json
.venv/bin/python -m video_freshness_lab --suite recovery --policy latest
.venv/bin/python -m video_freshness_lab --suite recovery --policy latest --session-filter --json
.venv/bin/python -m video_freshness_lab --scenario reconnect --queue-on-disconnect invalidate --session-filter --json
```

Full JSON schema version 2 includes config/control scripts, frame IDs, timestamps,
processing attempts and acceptance flags, drops/reasons, metrics, and ordered
events. `--scenario` selects a preset independently of `--suite`; `--suite`
selects the group when scenario is `all`. Config overrides must still satisfy
script ordering and horizon validation. API `None` disables monitoring/age
budgets; CLI overrides use integer milliseconds.

## Actual default-suite outputs

Defaults are FIFO/retain and filtering off except the `session-filter` preset.
Produced frames have identical IDs/timestamps under policy comparisons; all
differences below arise downstream of the same source/control schedule.
All age/time columns are virtual milliseconds. `null` means no emitted sample.

| Preset | Produced | Emitted | Drops | Obsolete outputs | Age violations | Max result age | No-progress alerts | Finished |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| normal | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 100 |
| consumer-slowdown | 10 | 10 | 0 | 0 | 6 | 250 | 0 | 340 |
| freeze | 6 | 6 | 0 | 0 | 3 | 150 | 1 | 240 |
| disconnect | 3 | 3 | 0 | 3 | 1 | 100 | 1 | 120 |
| reconnect | 7 | 7 | 0 | 3 | 5 | 190 | 1 | 280 |
| repeated-recovery | 9 | 9 | 0 | 6 | 7 | 220 | 2 | 360 |
| no-progress | 2 | 2 | 0 | 0 | 0 | 10 | 1 | 100 |
| obsolete-delivery | 5 | 5 | 0 | 1 | 3 | 150 | 0 | 200 |
| session-filter | 7 | 4 | 3 | 0 | 2 | 130 | 1 | 220 |

For the reconnect script the generated evidence is epoch 0, sequences 0–2, at
times 0/10/20, followed by epoch 1, sequences 0–3, at 60/70/80/90. Session start
events are at 0 and 55; the first epoch ends at disconnect time 25. With baseline
FIFO, its old outputs complete at 40, 80, and 120, both during disconnection and
after recovery. A successful output is therefore not proof of current provenance
in this explicitly permissive model.

## Equal-workload policy comparisons

Each row overrides only policy/filter options on the same source/control preset.
The `filter` mode checks both dequeue and completion. Drops include replacements
and session rejection; rejection is a subset, not an extra lost-frame category.

| Script | Policy | Emitted | Drops | Rejected | Obsolete outputs | Age violations | Max result age | Finished |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reconnect | FIFO | 7 | 0 | 0 | 3 | 5 | 190 | 280 |
| reconnect | latest | 4 | 3 | 0 | 2 | 0 | 70 | 160 |
| reconnect | FIFO + filter | 4 | 3 | 3 | 0 | 2 | 130 | 220 |
| reconnect | latest + filter | 2 | 5 | 2 | 0 | 0 | 50 | 140 |
| repeated-recovery | FIFO | 9 | 0 | 0 | 6 | 7 | 220 | 360 |
| repeated-recovery | latest | 5 | 4 | 0 | 3 | 0 | 60 | 200 |
| repeated-recovery | FIFO + filter | 3 | 6 | 6 | 0 | 1 | 100 | 240 |
| repeated-recovery | latest + filter | 2 | 7 | 4 | 0 | 0 | 60 | 200 |

Latest-frame buffering alone emits two obsolete-session reconnect results despite
zero 80 ms age violations. Session filtering alone removes old epochs but FIFO
still emits two over-age results. The properties require separate observations.
Combining latest-frame and session checks suppresses obsolete results in these
workloads, while deliberately emitting fewer outputs. That does not guarantee
availability, every-frame delivery, or sufficiently low age for another budget.

At reconnect time 55, source generation waits until the anchored tick at 60.
With filtered FIFO, active epoch-0 frame 0 completes at 40 and is rejected;
waiting old frames 1 and 2 are rejected at the same time without processing.
The model consumes processing resources for the rejected active item; it is not
cancelled. `frames_processed=5`, emitted=4, rejected=3 in this comparison.
With filtered latest, emitted=2, replacement drops=3, session rejects=2, and
processed attempts=3. Output age statistics exclude rejected results; raw
processing records retain their completion times and ages.

Optional queue invalidation removes waiting old frames at disconnect time 25
(two for FIFO, one for latest). It still leaves one old active result at time 40
when filtering is off. Completion filtering suppresses that result. Clearing a
waiting queue is therefore not equivalent to checking in-progress provenance.

The freeze preset produces no frames at 20–50 ms and resumes the same epoch at
60. Its watchdog alert is at 35 with `since_ms=10`. The long no-progress preset
alerts once at 25, not repeatedly for every missing tick; new evidence at 90
resets progress. A new epoch or production at an exact watchdog deadline wins
by event priority. Recovery policies and timeout definitions are deliberate test
conventions, not transport facts.

## Verification

The full suite passes 170 tests, including the original 54 Milestone 1.2 tests.
Recovery coverage includes session lifecycle/provenance, queued and active work,
reconnect/reset, multiple cycles, freeze, no-progress equality/reset, stale age
boundaries, start and completion filtering, explicit queue invalidation, duration
changes, ordered simultaneous controls, invalid scripts, and installed CLI JSON.
Across nine presets, both queue policies, filter on/off, and retain/invalidate,
tests verify conservation, unique drops, output provenance, and event chronology.

Every preset is also run with FIFO/latest and filter on/off for 100 repetitions
of each of the 36 combinations; full serialized evidence matches exactly in all
3,600 repeats. The tests forbid wall-clock/network calls in the repeat check.
This is a deterministic in-process repeatability result, not an integration
flake-rate or real-time performance benchmark. Sources are also verified identical
across all four policy/filter modes. Result-age maxima/means describe the emitted
sample; start-age statistics include all completed processing attempts. Both
must be read with drops and attempted-work records.

Before committing, run verbose pytest, Ruff lint and formatting checks, pip
integrity, working/staged whitespace checks, and full staged/history security
review. No runtime dependencies, media, camera settings, or external assets were
introduced. Python 3.11 syntax is preserved; local execution uses Fedora 3.12.15.
CI separately checks Ubuntu 3.11 and 3.12.

## Limitations, open questions, and next investigation

- Numbered evidence and an authoritative same-clock source head make lineage
  easy here. Pixel markers, sidecars/callbacks, decoder reordering, and unsynchronized
  clocks remain untested. There are no images, codecs, sockets, or real threads.
- Disconnect always retires a synthetic epoch; real transport reconnects might
  preserve a physical source session. Determining a trustworthy boundary is an
  external-adapter question, not answered by these scripts.
- Freeze is a producer pause, not duplicate-frame delivery. A real reader could
  keep returning the same pixels; unique-source and output-progress detectors
  would need separate instrumentation and tests.
- Age thresholds are observations, not enforced output suppression. Session
  filtering is strict with no grace period. Whether callers can carry comparable
  lineage through in-flight inference with a small adapter remains unknown.
- Retention/invalidation and priority rules define the model. Backend defaults,
  clock drift, scheduling noise, packet loss, GOP recovery, and corrupt frames
  may change the real behavior completely. Workload/event trace size is finite
  but grows with caller-selected production volume.
- The broader PRD threaded learning demo and thread-safe mailbox are still
  required before claiming full Stage 1 completion; no concurrency claims are
  made here. Later pixel identity and external audits retain their stage gates.
- No technical/adoption product gate is satisfied by demonstration code alone.
  Existing-library equivalence and external interest are still open. A recipe,
  upstream regression test, or closure remains a valid outcome.

Recommended next milestone: review the synthetic evidence contract and add the
PRD's thread-safe mailbox/clean-shutdown learning demo before introducing stamped
frames. Do not connect cameras or add RTSP dependencies until the intervening
PRD gates and scope are authorized. This recommendation is not implementation.

## Private delivery and security status

The private repository is `https://github.com/devAIsh88/video-freshness-lab`.
Foundation `6ff7cb3f7aec0ee50175b22f85d0ad8642d052d0` and Milestone 1.2
`d7b41a0b78fc6dc101624fc032be596044079e0f` were pushed and their remote branch
SHAs verified. Their GitHub Actions runs completed successfully:
[foundation CI](https://github.com/devAIsh88/video-freshness-lab/actions/runs/38469609425)
and [Milestone 1.2 CI](https://github.com/devAIsh88/video-freshness-lab/actions/runs/38470132139).
The Milestone 1.3 commit/push/CI verification follows this precommit snapshot and
is recorded in the final engineering report; no artificial status commit is used.

Both original PRDs remain unchanged and untracked, absent from Git history.
Licensing remains pending; private synchronization is not a public release.
No deployment, package/container publication, paid runners, or cloud provisioning
was added. The owner must configure/confirm Actions spending controls to prevent
unexpected standard-runner overage charges on the private repository.
