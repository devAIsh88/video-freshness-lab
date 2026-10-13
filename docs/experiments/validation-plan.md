# Stage 1 investigation and later validation gates

The investigation plan is broader than the implemented numbered-item experiments.
See [Milestone 1.2 observations](milestone-1.2-results.md). The authoritative
[PRDs](../prd/README.md) progress from numbered items to contracts, synthetic
frames, controlled faults, RTSP, external audits, and a product decision.
This plan describes that investigation without claiming the later stages are
authorized or complete.

## Facts, hypotheses, and assumptions

Confirmed repository facts: the PRDs select synthetic CPU-only validation,
event ordering before transport, reuse of existing sources, and CI only.
No external consumer has been tested here. The PRDs' claims about real failures
are research premises, not results produced by this repository.

Test these hypotheses rather than assuming them:

1. Healthy delivery/throughput can coexist with increasing evidence age or lag.
2. A bounded latest-item strategy reduces backlog under controlled overload;
   it does not by itself guarantee fresh final results after slow processing.
3. Freeze, disconnect, or restart can leave apparently successful stale outputs.
4. Explicit source epochs can reject old evidence even if sequence numbers reset.
5. A small adapter and deterministic oracle add value beyond existing-library
   configuration, GStreamer-native validation, or a short pytest/FFmpeg recipe.

Initial assumptions to make testable: a numbered source has an authoritative
head sequence, an injected clock, explicit epochs, and observable final-output
lineage. Real cameras may expose none of these reliably. Unknown lineage or
incomparable clocks must produce an inconclusive result, not a freshness pass.

## Proposed freshness definition

For an output from evidence `(epoch, sequence, produced_at)`, observe its
`emitted_at` and the authoritative head sequence of the same epoch at emission.
Define sequence lag as `head_sequence - sequence` and evidence age as
`emitted_at - produced_at` using one controlled monotonic clock domain.
Evaluate at final output, not just at dequeue. Frame-level observations can use
the same definition at consumption, but do not substitute for result freshness.

A violation occurs when comparable evidence exceeds the scenario's declared
maximum lag or age (strictly greater; equality passes), or belongs to an expired
epoch after the declared boundary. Each scenario declares numeric limits before
running; no universal freshness threshold is assumed. Negative age, future
sequence, impossible ordering, or missing lineage is invalid evidence, reported
separately from an observed stale result. Sequence lag cannot detect a stopped
source alone; a freeze test must also advance the controlled clock or observe
identity-progress deadlines. Do not infer production timestamps from decoder
arrival timestamps or compare unsynchronized host clocks.

## Proposed session boundary

A test session is an explicit source epoch with an identity that is not reused
when sequences reset. The controller's ordered restart/replacement event retires
epoch A and activates epoch B. For the initial strict synthetic rule, no output
from A may be emitted after activation of B, including already queued or in-flight
work. These are proposed oracle semantics for PRD Stage 2, not code in 1.1.

A disconnect is a transport event; it need not restart a physical source. A later
RTSP audit must document source identity, connection generation, and the event
that signals a trustworthy boundary. Reconnect-generation tagging is a possible
conservative adapter policy, not an RTSP protocol guarantee. Unknown boundaries
are inconclusive. Any alternative recovery/grace budget must be declared and
justified before the experiment, not adjusted after failure.

## Deterministic scenarios and controls

Use explicit steps or barriers and fake clocks before threads or sockets.
The rows below are proposed tests, with no measured outcomes yet.

| Scenario | Ordered stimulus | Evidence expected |
| --- | --- | --- |
| Baseline | Produce then consume each numbered item | Healthy delivery, zero lag, correct epoch |
| Overload (Stage 1) | Produce items 0–9 before one consume; max lag 1 | FIFO emits 0 with lag 9 despite delivery success; latest-item emits 9 with lag 0 |
| Slow final output (later contracts) | Dequeue latest item, advance source/clock, then emit | Final result can fail freshness even when dequeue was fresh |
| Freeze (later faults) | Repeat identity while injected clock passes declared age limit | Reads may succeed; identity/age exposes freeze |
| Disconnect (later faults) | Stop production, advance clock, then drain old work | Old evidence ages; no automatic new-source assumption |
| Restart (later contracts/faults) | Queue A, activate B, reset sequence, try to emit A | Old epoch rejected; B accepted only if otherwise valid |
| In-flight result (later faults) | Start processing A, activate B, finish A | Checks at final emission reject stale lineage |
| Cleanup (threaded lab) | Cancel while waiting or consuming | Workers terminate within a documented bound; no leaked threads |
| Invalid evidence (later contracts) | Missing epoch, negative age, future sequence | Explicit invalid/inconclusive verdict rather than false pass |

Pair failing demonstrations with valid controls. Avoid sleeps in pure metrics;
use barriers/events and bounded waits only for later thread cleanup tests.
Transport faults and backend-specific buffering remain PRD Stage 5 work.

## Existing solutions to investigate before building a package

These are candidates, not installed dependencies or completed audits:

- [GStreamer appsink](https://gstreamer.freedesktop.org/documentation/app/appsink.html)
  documents bounded/leaky queues. Test whether configured bounds plus downstream
  output checks already satisfy the declared contract.
- [GStreamer Validate](https://gstreamer.freedesktop.org/documentation/gst-devtools/gst-validate.html)
  offers pipeline validation tooling. Prefer native scenarios if they cover the
  required boundary without duplicating that system.
- [FrameGrab](https://github.com/groundlight/framegrab) is a camera/stream reader
  audit candidate. Pin a maintained revision and test configured behavior rather
  than treating the existence of reconnect code as a proof of result freshness.
- The PRDs also identify OpenCV buffering/timeouts, Frigate watchdogs, STARE,
  RidgeRun recovery, YERP, and commercial pipeline QA. Their precise guarantee
  overlap has not been verified here. Audit official docs and pinned code later.
- Reuse MediaMTX, fake-rtsp, or another existing synthetic source at Stage 5;
  source selection and suitability remain open. Do not implement a new server.

For each candidate, record revision, backend, configuration, queue policy,
boundary/clock semantics, output instrumentation, and positive/negative controls.
Compare minimally configured existing behavior against the proposed oracle.
An existing solution passing the same contract is useful negative gap evidence.

## Required evidence and go/no-go gates

Each later run records synthetic epoch/sequence, source-head sequence, age/lag,
event ordering, threshold, verdict, cleanup, platform, resolved dependencies,
backend, and configuration. Do not record private URLs, addresses, or media.
Missing source truth must be marked inconclusive, and simulator limitations explicit.

The full Stage 1 exit requires an alive FIFO freshness failure, deterministic
latest-item controls, validated pure metrics, explanations, and clean demo thread
shutdown. Milestone 1.1's import test satisfies none of those behavioral gates.

Before a standalone package decision, meet the DOCX gates:

- Reproduce at least one behavior in independent third-party code or an external
  application, with a conventional smoke pass alongside a freshness failure.
- Emit actionable session, sequence, lag, and event-order evidence.
- Keep a precise reference adapter approximately 30 lines or fewer, with documented
  instrumentation burden and clear value over a one-off pytest/FFmpeg script.
- Repeat mature event-order scenarios 100 times, with at most 1% unexplained
  failures; separate product failures from harness flakes without hidden retries.
- Obtain at least one external maintainer acknowledgment or accepted contribution
  and intent to use the contract from two unrelated developers.
- Show a maintenance/dependency burden proportionate to the small contract.

## Pivot or stop

Pivot to upstream tests or documentation if existing tools provide the same
guarantee with minimal configuration, or the core is only a short recipe.
Stop or simplify if only deliberately broken demo code fails, instrumentation
is invasive, lineage cannot be established, event-relative tests remain flaky,
or external maintainers reject the value. No detected defect must be published
as a negative result rather than treated as permission to invent a new feature.
Permitted outcomes are a validated package, upstream work, a reference recipe,
or closure. None is selected in this milestone.

## Milestone 1.2 and authorized next step

Milestone 1.2 implements deterministic numbered-item production/consumption,
FIFO/latest-frame buffering, virtual-clock metrics, and controlled slowdown.
The owner master task explicitly authorizes in-process session, freeze, and
interruption experiments in Milestone 1.3 after 1.2 acceptance. This is a scope
decision for synthetic evidence; realistic disconnect/restart transport, stamped
images, threaded demos, external audits, and productization retain their PRD
gates. No cameras, OpenCV, servers, or network capture are required here.
