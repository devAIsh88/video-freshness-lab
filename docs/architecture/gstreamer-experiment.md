# Finite GStreamer experiment

Milestone 1.7 tests an existing library before considering a custom reliability
layer. Native appsrc/appsink was selected from the
[1.6 capability investigation](../research/existing-library-capability-matrix.md):
its explicit queue controls and counters make native equivalence testable. This
is an optional local research harness, not a transport adapter, plugin framework,
decoder, or production sink. The existing simulator, mailbox, and session
pipeline are unchanged. The owner authorized only this local milestone.

## Preflight and existing dependencies

Verified on Fedora 44: `gst-inspect-1.0` and `gst-launch-1.0` report **1.28.6**;
appsrc/appsink's `app` plugin also reports **1.28.6**. `/usr/bin/python3` is
**3.14.7**, with PyGObject **3.56.3**, Gst 1.0 and GstApp 1.0 introspection.
The project venv remains **Python 3.12.15**, without `gi`. CI remains Python
3.11/3.12. These are distinct interpreters; successful system imports do not
imply venv imports. No packages, RPMs, venv settings, or system settings changed.

Already installed optional experiment prerequisites, inspected with RPM metadata:

| Component | Installed version | Purpose | Package license/source |
| --- | --- | --- | --- |
| `gstreamer1`, `gstreamer1-plugins-base` | 1.28.6-1.fc44 | Native pipeline, appsrc/appsink and introspection data | LGPL-2.1-or-later; installed Fedora RPMs, [GStreamer](https://gstreamer.freedesktop.org/documentation/) |
| `python3-gobject`, `python3-gobject-base` | 3.56.3-1.fc44 | Existing system Python GI bindings | LGPL-2.1-or-later; installed Fedora RPMs |
| `gobject-introspection` | 1.86.0-3.fc44 | Introspection infrastructure | RPM expression: GPL-2.0-or-later AND LGPL-2.0-or-later AND LGPL-2.1-or-later AND BSD-2-Clause |

These external component licenses do not choose this repository's license.
`gstreamer1-plugins-base-tools` was queried and is not installed; it is not needed
for this direct in-process pipeline. Missing prerequisites on another host are
a dependency gate, not permission to install packages. Do not install PyGObject
into the project venv or alter system packages automatically.

```sh
gst-inspect-1.0 --version
gst-inspect-1.0 appsrc
gst-inspect-1.0 appsink
gst-launch-1.0 --version
/usr/bin/python3 --version
/usr/bin/python3 -c "import gi; gi.require_version('Gst', '1.0'); gi.require_version('GstApp', '1.0'); from gi.repository import Gst, GstApp; Gst.init(None); print(Gst.version_string())"
```

Required properties are verified rather than silently substituted: appsink
`leaky-type`, `max-buffers`, `in`, `out`, `dropped`, and queue occupancy are present.
Appsrc also has its own internal queue, limits, and counters. The runner fails
if required properties or bindings are missing; it has no integration skips.

## Pipeline and controlled variables

Direct **appsrc → appsink**, no intermediate elements, extra queue, clock sync,
video codec, network, display, camera, or media file. Each case is a fresh pipeline
inside a fresh subprocess using the selected system interpreter.

| Element | Exact settings |
| --- | --- |
| appsrc | `max-buffers=4 max-bytes=0 max-time=0 block=false leaky-type=none format=time is-live=true do-timestamp=false`; caps `application/x-vfl-synthetic` |
| appsink | `max-buffers=2 max-bytes=0 max-time=0 sync=false async=false emit-signals=true enable-last-sample=false wait-on-eos=false`; `leaky-type=none` (FIFO) or `downstream` (oldest waiting drop) |

Conditions A/B use native FIFO/leaky respectively. Conditions C/D use identical
native settings and media, adding only the application final-output epoch check.
No custom waiting mailbox is inserted. Appsrc's nonblocking limit is not a
generic producer throttle: at most four buffers are submitted in these finite
scripts. Its actual queue levels and counters are recorded separately.

## Identity, time, and publication

Each 13-byte buffer contains a fixed synthetic magic plus an unsigned 64-bit
token. Before pushing, the producer registers that token against frozen
`FrameEvidence` containing source alias, epoch, sequence, PTS and provenance.
At ingress and acquisition the entire payload is decoded and looked up exactly.
Unregistered/invalid payloads fail, rather than guessing an epoch from order,
pixels, or PTS. Duplicate acquisitions and changed PTS fail. This explicit local
registry is trustworthy only for this direct synthetic path; codec/image lineage
is not established. Registry construction is experiment scaffolding, not an
approximately 30-line adapter proven on an independent application.

Tokens are 0–3. Epoch 0 uses sequence equal to token. For epoch workloads tokens
2/3 explicitly belong to epoch 1 and sequences 0/1. PTS is sequence × 10 ms,
in nanoseconds (`Fraction(1, 1_000_000_000)` seconds/tick); duration is 10 ms.
Resetting PTS does not change the GStreamer pipeline or stream identity. The
application controller alone declares the logical epoch transition.

Submission, sink-pad observation, application receipt, processing start, and
decision times use `monotonic_ns()` in one process domain. Application receipt
is measured after `try-pull-sample` returns. Pad-to-receipt includes waiting in
the native sink path; submission-to-receipt also includes appsrc/native scheduling.
Arrival age is decision minus receipt; processing delay is decision minus start.
PTS is a separate media clock. No subtraction of PTS from local monotonic time,
physical capture time, capture latency, or cross-process clock comparison occurs.
Every capture age is explicitly unavailable (`null`).

The consumer and controller are split phases on the owner thread: acquisition
starts a processing attempt, which may be held while the native streaming task
continues and the controller changes epoch. Completion happens afterward. This
models in-progress work without adding an inference worker or pretending to
measure inference throughput. Native GStreamer work is asynchronous; no arbitrary
sleep proves a boundary. A small `PublicationLedger` validates epoch and appends
the observable output decision under one lock, following 1.5. Historical source
admission remains separate from final rejection. This ledger is an experimental
in-memory sink, with no guarantee for an external callback/network/UI sink.

## Workloads and synchronization

Each native `new-sample` callback increments an observation counter after queue
insertion; it does not consume. A sink-pad probe observes ingress before queue
handling. Condition predicates and bounded waits establish the following order:

| Workload | Script, common to native-only and filtered pair |
| --- | --- |
| Balanced | Push one token, wait for insertion, acquire/complete; repeat four times |
| Slow | Acquire token 0 and withhold completion; submit 1–3 while further pulling is withheld; then complete 0 and drain |
| Finite producer pause | Balanced 0/1; record empty nonblocking pull and paused phase; resume balanced 2/3. Event-delimited finite pause, no minimum elapsed-duration or freeze claim |
| Buffered epoch | Insert 0/1 without pulling; declare epoch 1; submit 2/3; then drain |
| Active epoch | Acquire 0, insert 1; declare epoch 1; submit 2/3; complete old active 0 and drain |
| Pending shutdown | Insert 0/1, send EOS, observe bus EOS with two samples pending under `wait-on-eos=false`; transition NULL without pulling |

FIFO becomes full before the entire burst can enter appsink: its native task
blocks during queue admission, leaving a buffer in transit and sometimes one in
appsrc. Leaky admits the whole burst while dropping waiting items. Consequently
media IDs, PTS and application phase schedule match across A/C and B/D, but actual
native scheduling differs between FIFO/leaky. Entry is not insertion. The
controller waits for FIFO's reachable insertion/ingress boundary, not an
impossible fully inserted burst in a full nonleaky queue. Results are not a
prediction of the discrete-event simulator.

## Metrics and termination

The final counters are read after EOS and the declared drain/stop boundary, before
NULL resets native state. Each individual property read is independent; snapshots
are labeled `atomic=false`. Intermediate samples may disagree during transfers
and give only observed occupancy, not a global maximum. Stable final conservation:

```text
submitted = received + native_drops + unpulled_at_shutdown
received = published + application_rejected
appsrc forwarded = submitted; appsrc pending = appsrc dropped = 0
```

Native drops affect buffers never acquired; application rejections affect
successfully processed acquired samples. They never double-count one frame.
Pending samples intentionally abandoned at NULL are a separate category, not
reported as native leakage, processing success, or session rejection. Error cases
report raw ingress/receipt/decision traces and a failed status rather than
fabricating complete conservation or calling failed processing a rejection.

Normal EOS uses `wait-on-eos=false` so bus EOS does not require an absent consumer
to drain. Separate integration controls set it true, observe EOS at the sink pad
while two samples remain, verify no bus EOS is recorded at that boundary, drain,
then require bus EOS. This finite control does not quantify an indefinite hang.
Error polling retains EOS; a poll restricted to ERROR would discard other bus
messages. Bus error domain/code/message are captured; debug text is omitted.

Every pipeline enters NULL in `finally`, checks state with a 3-second guard,
disconnects instrumentation, and reports extra Python threads. No application
worker threads are created. Native streaming tasks are stopped by NULL; each
subprocess then exits, containing any remaining native/global runtime resources.
The supervisor has a 15-second process timeout covering even stuck native calls,
and kills/waits the child on timeout via `subprocess.run`. Guards are hang
safeguards, not correctness timing budgets. Cases never silently retry.

## Reproduction and test separation

```sh
# Explicit optional integration: 24 comparisons plus EOS/error controls.
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -v
# 20 independent subprocess repetitions of each of 24 configurations.
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.gstreamer_experiment --repeat 20 > /tmp/vfl17-results.json
# Normal mandatory suite, with no GI requirement or integration skips.
.venv/bin/python -m pytest -v
```

`PYTHONPATH=src` is explicit source access for system Python's optional experiment;
it does not change project installation or mask the venv's editable-import test.
Integration lives outside pytest's configured `tests` directory and uses stdlib
unittest so system pytest is unnecessary. Ordinary CI executes pure helpers and
existing tests, not GStreamer. The report must name both command results separately.
Missing runtime prerequisites fail the explicit integration command.

Official reference context: [appsink queue/EOS controls](https://gstreamer.freedesktop.org/documentation/app/appsink.html)
and [appsrc's internal queue](https://gstreamer.freedesktop.org/documentation/app/appsrc.html).
Measured claims and limitations are in [the 1.7 report](../experiments/milestone-1.7-results.md).
