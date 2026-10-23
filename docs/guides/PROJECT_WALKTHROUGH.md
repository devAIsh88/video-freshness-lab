# Project walkthrough

## The problem

A camera application can be connected, return images and produce predictions
while describing the past. A successful read proves delivery. It does not tell
us when the image was captured or whether its source is still the active source.
This project investigates how to test that distinction using controlled evidence.

A producer creates frames. A consumer takes frames and performs work, such as
inference. A buffer holds frames while the consumer is busy. Throughput counts
completed work per second; latency measures elapsed time through a path.
Freshness asks whether the evidence behind a particular result is still useful
at the moment that result is published. Those questions need different metrics.

RTSP is a protocol for controlling a media session. RTP carries the media. Our
local experiment carries RTP and RTCP inside an RTSP TCP connection, then decodes
JPEG images with GStreamer. Queues can exist in the source, transport, decoder,
application and result-processing stages. Observing one queue cannot prove that
all upstream delays are bounded.

## FIFO and the latest waiting item

FIFO means first in, first out. It preserves waiting order. If the producer is
faster than the consumer, old frames wait longer while every processing attempt
can still succeed. In the virtual slow-consumer fixture, ten FIFO results reach
310 ms maximum result age and eight exceed the declared 80 ms budget.

A latest-item policy stores at most one waiting item and replaces it when a newer
item arrives. Under the same source schedule, the consumer processes sequences
0, 4, 8 and 9, replacing six waiting items; maximum result age is 70 virtual ms.
That passes the fixture's 80 ms budget. With a 30 ms budget it still fails all
four results. A small queue is a mechanism, not a universal freshness guarantee.

The threaded mailbox repeats the handoff with actual Python threads and explicit
events. Its controlled slow mode accepts ten items, delivers 0 and 9, and replaces
eight. These counts are enforced by synchronization. They are not a throughput
benchmark or an estimate of normal operating-system scheduling.

## An old result can outlive its session

An epoch is an application-owned generation number. Suppose epoch 0 frame A is
already in processing. The controller retires epoch 0 and activates epoch 1.
Replacing the waiting queue cannot remove A from the processor's local variable.
When A finishes, publishing it without another check emits an obsolete result.

The final check compares A's original epoch with the current epoch. Validation
and recording the output happen under the same lock. If the transition wins that
lock first, the old completion is rejected. If publication wins first, it belongs
to the earlier legal order. The rule does not pretend to cancel arbitrary work
already running, or to make an external database/network transaction atomic.

Closing the source is different: the mailbox stops accepting input and drains
its final waiting item once. Closure alone does not invalidate the epoch.
Application shutdown separately disables publication while preserving this drain
contract. Processing callbacks must cooperate with shutdown and eventually return.

## Evidence travels with the work

The immutable FrameEvidence record separates several observations:

| Evidence | Meaning | What it does not establish |
| --- | --- | --- |
| Source/session marker | A source identifier and epoch with stated provenance | Authenticated physical camera identity by itself |
| Sequence | Source order or a local delivery ordinal, explicitly labeled | A local ordinal cannot detect repeated source images |
| Local receipt time | When this process observed a frame | Time spent in upstream buffers |
| Decoder PTS | Presentation timestamp in a media timeline | Physical exposure time or a shared wall clock |
| Capture timestamp | Capture meaning and clock mapping supported by evidence | It must not be filled with PTS or receipt time by assumption |
| Application epoch | Which logical generation the controller admits | Whether the physical camera restarted |

The pure diagnose function receives the current context and an explicit clock;
it does not read a clock or publish outputs. Its session and age answers are
independent. An obsolete result may have a recent receipt timestamp. Missing
capture evidence yields UNKNOWN, not zero age. Source sequence lag requires a
trustworthy source head, which the unstamped RTSP stream does not expose.

## Why actual stamped images mattered

Numbered objects establish queue semantics but do not establish identity through
image processing. Stage 3 creates actual NumPy BGR image arrays. Before buffering,
the source writes a visible label and a binary source/epoch/sequence marker with
a checksum. The experiment reads that marker after OpenCV color conversion and
lossless PNG encode/decode, then checks it against the original immutable sidecar.

A new decoded array can contain the old marker. That is different from no new
array arriving, a queued old frame, or a late result from a retired epoch. A
static scene can also produce new images, so the static-scene control advances
its markers while keeping a scene region unchanged. We do not call identical
scene pixels a camera freeze without better evidence.

The external audit later verified these markers through FFV1 video encoding,
FFmpeg decoding and FrameGrab's actual file-consumer path. This adds one tested
video codec path; it does not establish marker survival through JPEG RTSP or
arbitrary resize/crop operations. A crop removing the marker makes identity UNKNOWN.

## Why GStreamer, and why the PIVOT

GStreamer is an existing media pipeline library. Its appsink component exposes
decoded buffers to applications and supports native queue limits, downstream
leaking and drop counters. Existing Fedora bindings made a small finite test
possible. FFmpeg, PyAV and OpenCV were compared in the capability matrix, but
only the documented/executed scope of each is claimed.

The native comparison showed that GStreamer already replaces old waiting buffers
with the selected settings. Adding another custom mailbox around that native
queue did not have demonstrated value. Native buffering could not retract an
already acquired result; the application epoch check covered that boundary.
The project therefore pivoted to native configuration plus a minimal output
policy and validation recipe. Further experiments did not overturn that decision.

## What actual RTSP established

The installed GstRtspServer library provides generated test-pattern JPEG media.
The client transports it over IPv4 loopback TCP, decodes it, acquires a GstSample,
attaches a frozen receipt sidecar and passes that same evidence to the final
publication ledger. The RTSP and epoch tests therefore exercise a connected path.

The mature Stage 5 cohort passed 1,200/1,200 trials: normal, held-result transition
and reconnect, four queue/filter combinations, 100 repetitions each. Filtered
modes rejected all 400 obsolete completions. All 400 obsolete publications occurred
in intentionally permissive controls. Explicit application reconnect succeeded
400/400 times. This is not automatic camera reconnection or a public-network rate.

The first mature baseline had one server teardown SIGSEGV in 400 trials. It remains
in the report. Explicit media/session/client/pool cleanup was added; the corrected
cohort is reported separately. Neither that change nor successful repeats proves
race freedom or establishes an upstream defect's root cause.

A separate 720-trial transport assessment delayed or stalled interleaved media
records and cut owned TCP connections. It includes repeated recovery, slow
consumption and blocked-read shutdown. These are controlled delivery impairments;
no UDP packet-loss or physical-network equivalence is claimed. Source capture time
and physical freshness remain UNKNOWN throughout the unstamped RTSP experiments.

## What the independent audit found

FrameGrab is an external maintained camera/file consumer, not code written for
our demonstration. The audited commit and MIT license are pinned in the report.
Its supported file replay, frame decimation, seek, EOF and crop behavior matched
the inspected implementation in the final 800-trial cohort, 100 per scenario.
No reusable freshness defect was found under those conditions. The final check
rejected old held results only because our application explicitly chose that policy.

An earlier 100-trial cohort recorded one immediate native-task remainder after
release. The final cohort used a predeclared one-second bounded observation against
a fixed task baseline and passed; the earlier failure is retained. A reproducible
README check also reported GStreamer support when OpenCV's actual value was NO.
A private correction proposal exists; nothing was posted upstream.

## What each original stage accomplished

| Original stage | Contribution | Remaining boundary |
| --- | --- | --- |
| 0 | Requirements, differences, privacy and stop gates | Original documents remain draft owner inputs, not public artifacts |
| 1 | FIFO/latest learning model and clean threaded demonstration | Windows execution unverified |
| 2 | Frozen evidence, unknowns, event order and final logical-epoch validation | No physical-session inference or external-sink transaction |
| 3 | Real source-stamped synthetic images and transform verification | Only selected transforms/codecs verified |
| 4 | Slowdown, backlog, no-data, repeated identity, restart, recovery and cleanup controls | No general real-camera freeze detector |
| 5 | Real JPEG/RTP/TCP receipt-to-output contract and mature local repeats | No physical capture truth, UDP impairment or broad network claim |
| 6 | Actual independent FrameGrab file audit, native guarantees and honest negative result | External RTSP blocked; no acknowledgment/adoption |
| 7 | Review of every gate; choose reference recipe/toolkit | Package release remains unapproved and unsupported by demand evidence |

## Final outcome

Keep the documented reference recipe and validation toolkit. Stop active feature
work at this handover. A reusable pytest package is deferred: complete semantic
instrumentation is not shown to fit the approximately 30-line goal, value over a
short application-specific test is unproven, and no maintainer acknowledgment or
two-developer adoption evidence exists. The owner approved MIT source publication
following the research handover; package publication remains unapproved. Research
has produced useful positive and negative evidence without turning unknown
freshness into a success claim.
