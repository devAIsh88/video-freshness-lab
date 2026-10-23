# Project explanation and questions

## A 30-second introduction

“Video Freshness Lab studies a failure that ordinary health checks miss: a video
application can keep returning frames while its results describe old evidence.
We built deterministic queue and session experiments, then tested the same
application epoch rule through actual local RTSP decoding. Native GStreamer
buffering handled waiting frames, so the outcome is a reference recipe and test
toolkit rather than another streaming framework. Physical capture freshness and
external adoption remain unproven.”

## A 90-second explanation

“A successful read tells us that an image arrived. It does not tell us how old
that image is or whether it belongs to the source generation we still accept.
First we modeled a fast producer and slow consumer. FIFO preserved order but
accumulated old work. A latest-item buffer replaced waiting frames, reducing lag.

“The second problem appears during restart. An old frame may already be in
processing when a new session starts. Clearing the queue cannot retract it.
We retain its original immutable evidence and check its epoch again at final
publication, under the same lock that changes the epoch.

“We verified actual source stamps through OpenCV transformations, native
GStreamer queues, and decoded receipt evidence over localhost JPEG/RTP/TCP.
The mature corrected RTSP cohort passed 1,200 trials, with 100 per configuration;
the report retains an earlier teardown failure. An independent FrameGrab file
audit also ran 800 trials, found supported native behavior and no demonstrated
freshness defect, plus a small documentation-check issue.

“The final decision is to retain native buffering and a minimal output policy.
We have no evidence for a new package's adoption or a universal capture-freshness
guarantee. Unknown capture time stays UNKNOWN.”

## A five-minute technical presentation

**Minute 1 — define the question.** A producer creates images and a consumer
processes them. Throughput measures how much work completes, while freshness asks
how current the evidence behind a particular published result is. Those can move
in opposite directions. Show the virtual slow FIFO result: all ten frames are
processed, but maximum result age reaches 310 injected ms and eight exceed the
chosen budget. The process is healthy by a basic smoke check.

**Minute 2 — explain the two boundaries.** A latest-item buffer keeps one waiting
frame. It cannot change the frame currently held by a consumer. Under the same
virtual schedule it processes 0,4,8,9 and has 70 ms maximum age. Now draw an epoch
transition while frame A is in processing. The application must validate A's
original epoch when publishing, not just when acquiring it. The example checks
and appends to its in-memory output ledger under one lock. Closure drains input;
shutdown and epoch invalidation are separate policies.

**Minute 3 — explain evidence and test design.** FrameEvidence is immutable. It
labels sequence provenance, local receipt time, decoder PTS and capture time
separately. A timestamp's units are insufficient: clock origin and meaning must
also be known. The diagnostic therefore has separate session and age statuses,
and unknown capture evidence is not replaced with a recent receipt. Virtual
clocks and explicit events control ordering. NumPy/OpenCV frames carry markers
created before buffering; the decoder must recover the same source/epoch/sequence.
Repeated old stamps, static scenes and missing new data have different controls.

**Minute 4 — explain real-library evidence.** GStreamer's appsink already supplies
bounded/leaky waiting queues and counters. We did not build another runtime queue
layer around it. The local RTSP fixture uses the installed server and real JPEG
encoding, RTP-over-TCP and decoding. A decoded GstSample's receipt evidence reaches
the same final epoch ledger. The corrected mature cohort passed 1,200/1,200 with
100 per configuration and 400 explicit recoveries. A separate 720-trial delivery
fault cohort covers delay, stall, cuts and bounded shutdown. The initial server
teardown failure remains in the report; successful repeats do not prove race freedom.

**Minute 5 — explain the external audit and decision.** FrameGrab's existing file
consumer was pinned, reviewed and run unchanged. Our generated markers survived
FFV1 encoding and FFmpeg decoding; native decimation, replay, seek, crop and EOF
matched supported behavior. No reusable freshness bug was found. A misleading
README backend check has an unposted proposal. Complete semantic instrumentation
is larger than the thin 15-line adapter wrapper, and external adoption evidence is
absent. We choose the documented recipe/toolkit, retain the PIVOT, and stop feature
work. The research process is complete with explicit unmet external gates; package
release and broad camera freshness validation are not approved.

## Implementation milestones, without confusing them with PRD stages

| Increment | What to explain |
| --- | --- |
| 1.1 | Repository foundation, requirement conflicts, private source documents and CI-only rules |
| 1.2 | Virtual FIFO/latest comparison, explicit ages/lag and deterministic metrics |
| 1.3 | No-data freeze, disconnect/reconnect, held old work and session-filter controls |
| 1.4 | Condition-based one-slot mailbox, finite worker ownership and drain-on-close |
| 1.5 | Locked final epoch boundary, held-result and legal-order tests |
| 1.6 | Immutable evidence, timestamp provenance, UNKNOWN and library capability comparison |
| 1.7 | Existing GStreamer queues/counters; evidence supporting PIVOT to native buffering |
| 1.8 | Real local RTSP JPEG/RTP/TCP, decoded receipts, explicit reconnect and NULL cleanup |
| 1.9 | Fixture-only TCP delay/stall/cut assessment, separate from application faults |
| Original Stage 3/4 follow-up | Actual stamped images and repeated decoded-content control; numbered objects were insufficient |
| Original Stage 5 follow-up | 100/config mature RTSP runs and explicit native teardown correction |
| Original Stage 6 | Genuine FrameGrab file-consumer audit and honest negative freshness result |
| Original Stage 7 | All gates reviewed, recipe/toolkit chosen, owner handover and stop |

## Twenty likely technical questions

1. **What is the project's actual contribution?** An explicit evidence vocabulary,
   controlled regression examples, native buffering comparisons, and final epoch
   validation at publication. It makes missing evidence and policy boundaries
   visible. It does not establish a new capture-library gap.

2. **Why isn't FPS enough?** A consumer can process old queued frames at a steady
   rate. FPS counts delivery/completion; source identity, lag and age describe
   the evidence behind each result.

3. **What is sequence lag?** Distance from a trustworthy source head to the frame
   being evaluated within the same source/epoch. It is not elapsed time. The
   simulator owns a source head; the unstamped RTSP path does not, so its source
   lag is UNKNOWN.

4. **Does latest-frame guarantee freshness?** Only waiting capacity is bounded.
   An active computation and upstream buffers may still be old, and a strict
   age budget may still fail. Our 30 ms budget control demonstrates this.

5. **Why not just clear the queue on reconnect?** An acquired frame is outside
   the queue. Its delayed result still needs a final epoch check.

6. **What exactly is an epoch?** A controller-owned logical generation. It lets
   the application retire old work. It is distinct from an RTSP connection,
   decoder PTS domain or proven physical camera restart.

7. **Why are the evidence records immutable?** Processing must retain the
   original source observations. Replacing the epoch or timestamp at completion
   would disguise old evidence as new. Frozen dataclasses also make tests and
   ownership easier to inspect; they do not automatically freeze arbitrary arrays.

8. **How are arrays protected?** The image experiment creates a read-only view
   backed by immutable bytes. The frame sidecar is frozen separately. Source
   markers are decoded again after the tested transformation.

9. **How does the final check avoid a race?** Validation and ledger insertion use
   the same lock as epoch transition. The tests assert the two legal orders.
   An external network/database sink would require an additional transaction or
   publication protocol; the current lock does not cover it.

10. **Does the GIL make locks unnecessary?** No. The contract spans multiple
    operations and blocking/native work can release the GIL. A Condition protects
    mailbox state; a Lock protects epoch validation and publication ordering.

11. **Why use a Condition rather than polling?** A condition wait releases its
    lock while blocked, wakes on state changes and rechecks a predicate. close
    wakes waiters. Explicit waiting boundaries also make tests reproducible.

12. **What does close mean?** Stop accepting new frames and drain one pending
    item. It does not retire the current epoch. Application shutdown additionally
    suppresses publication and depends on cooperative processing termination.

13. **How do tests avoid fragile sleeps?** Virtual time, injected clocks, events,
    wait predicates, pipe acknowledgments and finite process guards establish
    ordering. A timeout bounds a hang. The external native-task observation polls
    a real predicate within a declared one-second guard; waiting alone is not a pass.

14. **How do you distinguish a freeze from a static scene?** The controlled
    source supplies identity. New decoded arrays repeating an old marker differ
    from advancing markers over an unchanged scene region. Without trustworthy
    source identity, equal pixels alone are inconclusive.

15. **What is RTSP versus RTP?** RTSP controls the session; RTP carries media and
    RTCP carries related control/reporting. The fixture interleaves media records
    on TCP. TCP observations are not UDP packet-loss evidence.

16. **Why GStreamer?** Existing Fedora bindings and native appsink queue/drop/
    timestamp controls support a small measurable experiment. The choice follows
    inspected capabilities, not a claim that other backends cannot work.

17. **Does PTS tell us when an image was captured?** It is a presentation stamp
    in a media timeline. Capture semantics and clock mapping need independent
    evidence. Local receipt is another distinct boundary; none is substituted.

18. **What does 1,200/1,200 prove?** The corrected declared local configurations
    completed with zero observed unexplained failures in that cohort, 100 each.
    It does not prove a zero underlying failure probability, all race freedom or
    real-camera/network reliability. The earlier 399/400 cohort remains separate.

19. **Did you find an upstream bug?** A README GStreamer support predicate has a
    reproducible false positive; a private correction proposal exists. No runtime
    freshness defect was observed in the tested file consumer. Nothing was posted
    and no maintainer acknowledgment or adoption was obtained.

20. **Why not publish a pytest package now?** Complete precise instrumentation
    is not shown to fit the approximately 30-line goal, unique value over a short
    test is unproven, and demand gates are unmet. Licensing/publication also need
    owner approval. A reference recipe is a legitimate PRD outcome.

## Difficult design questions

**Did the experiments simply build something designed to fail?** Early controls
intentionally expose queue/session behavior. They are labeled demonstrations.
Native GStreamer, real local RTSP decoding and unchanged external FrameGrab add
separate evidence. The external audit honestly found supported behavior rather
than manufacturing a defect to justify a product.

**Are the 15-line and 24-line adapters enough to pass the PRD size gate?** They
are thin wrappers. FrameGrab's 15-line observe function depends on marker decoding,
source stamping and final policy wiring; the whole audit is 368 lines including
measurement/supervision. The 24-line RTSP receipt helper has narrower semantics.
The full independent semantic-instrumentation gate remains PARTIAL, not PASS.

**Was the initial cleanup failure hidden by changing the assertion?** No. Its
99/100 cohort, failed observation and raw hash remain. A separate predeclared
cohort uses a fixed native-task baseline and bounded disappearance observation.
That avoids equating an immediate snapshot with a sustained leak. Exact cause
of the earlier remainder is still unknown.

**Why JPEG rather than H.264?** JPEG keeps the finite RTSP codec path small and
independently decodable. A GOP is a group of pictures with dependencies in codecs
such as H.264; decoder reordering, reference frames and recovery would add separate
evidence requirements. Those behaviors were not validated by this JPEG fixture.

**Could native flushing replace the final epoch check?** Flushing may remove
native queued work. It cannot generally mutate or revoke an array already held
by arbitrary application code. A final application policy remains necessary if
that application promises suppression after its own transition boundary.

**Can the project be used for a safety claim?** No. It does not validate physical
capture clocks, real camera behavior, hardware/network faults or organizational
safety processes. The useful claim is bounded regression evidence for stated
contracts, with unknowns explicit.

## Remaining research, only if separately authorized

Independent real-camera work would need trustworthy source identity/capture-clock
semantics, clock uncertainty, codec/GOP coverage, native timestamp continuity,
physical disconnects and resource ownership under faults. External RTSP audit
needs a reviewed OpenCV/GStreamer-compatible environment. Windows needs actual
execution. Package reconsideration needs independent low-burden integrations,
clear value over recipes, maintainer acknowledgment and two unrelated interested
developers. None is an automatic next milestone.
