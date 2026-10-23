# Final go/no-go decision

Decision: **PIVOT — retain a documented reference recipe and validation toolkit;
stop active feature development at this handover.** A reusable pytest package is
NO-GO on present evidence. Productization may be reconsidered only after the
specific unmet gates below are independently satisfied.

Date: 2026-10-23. Both original v0.1 PRDs were read completely. This reviews the
original Stage 7 exit criterion; it does not reinterpret every missing product
gate as a research failure or assume a package is the desired result.

## Original hypothesis and observed result

A small CI contract might reveal expired or previous-session results despite
successful reads, require little instrumentation, and offer enough independent
value to become reusable. The lab establishes the distinction and a useful
application publication rule. It does not establish broad demand or a generic
low-burden source-freshness adapter.

The virtual/threaded cases demonstrate backlog and held obsolete work. Stamped
images establish identity through selected transforms. Existing GStreamer queues
provide the needed waiting-buffer policy. Actual local JPEG/RTP/TCP receipts
exercise the final logical epoch check, with measured repeatability. Controlled
TCP impairments show finite failure/recovery and cleanup evidence. The unchanged
external FrameGrab file consumer supplies independent behavior and an honest
negative freshness-defect result. See [consolidated evidence](../experiments/FINAL_RESEARCH_REPORT.md).

## Technical gate review

| Gate | Classification | Evidence and effect on decision |
| --- | --- | --- |
| Smoke succeeds while stale evidence is detected | PASSED in controlled paths | FIFO backlog; repeated old source stamps; held old completion despite recent receipt |
| Contract detects intended stale epochs | PASSED for declared application boundary | Locked ledger and original sidecars; filtered mature RTSP has zero obsolete publications |
| Session/sequence/lag/event diagnostics | PASSED where observable; UNKNOWN fields explicit | Synthetic source markers/lag; native connection/application distinction; RTSP capture/source lag UNKNOWN |
| Approximately 30-line precise reference integration | PARTIAL / full reuse gate NOT MET | RTSP receipt helper 24 lines, external observe 15, but marker/source/policy support exceeds these wrappers; complete generic semantic burden unproven |
| At least 100 mature repetitions, at most 1% unexplained failures | PASSED for final declared cohorts | 100 each of 12 RTSP configurations and eight external scenarios; initial failures retained separately |
| Real independent external behavior | PASSED within supported file path | Pinned maintained FrameGrab, FFV1/FFmpeg decode, native replay/decimation/seek/EOF/crop |
| Clear added value over basic pytest/FFmpeg | UNKNOWN as a package advantage | Evidence vocabulary and recipe are useful; a one-off test can cover the observed external path |
| General source capture freshness | UNKNOWN / NOT VERIFIED | No trusted camera capture clock or physical source epoch; no universal freshness verdict |
| Cross-platform learning implementation | PARTIAL | Fedora and Ubuntu Python CI verified; Windows execution NOT TESTED |
| External RTSP consumer execution | BLOCKED in audited environment | OpenCV wheel reports GStreamer: NO; no new native build or privileged install undertaken |

Zero observed failures in a finite cohort is not a universal zero failure
probability. Initial mature RTSP 399/400 with one server -11 exit and initial
external baseline 99/100 with one immediate native-task remainder remain separate.
The native server teardown was explicitly corrected before a fresh cohort; the
external cleanup observation was revised and predeclared before its fresh cohort.
Neither is a hidden retry or proof of an upstream defect's root cause.

## Adoption and sustainability gates

| Gate | Classification | Actual evidence |
| --- | --- | --- |
| External maintainer acknowledgment / accepted related contribution | NOT ACHIEVED | No communication sent or acknowledgment received; private README proposal only |
| At least two unrelated developers intending to run the contract | NOT ACHIEVED / NOT TESTED | No genuine adoption evidence recorded |
| Proportionate maintenance burden | PASSED for private recipe scope; UNKNOWN for package | Stdlib core, optional image pins; GI/plugin/version/platform matrix remains a support cost |
| Public license selected and redistribution approved | BLOCKED pending owner decision | Repository license remains pending; third-party source/binaries are not redistributed |
| Public release / package publication approved | NOT APPROVED | Current instructions authorize private research delivery only |

No response from people who were never contacted is counted as rejection or lack
of interest. No simulated feedback is counted as adoption. Existing dependency
licenses do not select this repository's license. The large eager-import surface
of the external audit remains confined to a disposable environment, not added to
our package requirements.

## Evaluation of the four permitted outcomes

| Outcome | Decision | Reason |
| --- | --- | --- |
| Reusable pytest package | Reject for present scope / DEFER reconsideration | Adapter burden, differentiating value, portability, demand and licensing gates remain unmet |
| Upstream contributions plus audit | Retain as an optional future route, not claimed delivery | Audit complete; one documentation proposal prepared; no external submission authorized or accepted |
| Documented reference recipe and validation toolkit | **SELECT** | Matches native buffering findings, small application output policy, reproducible controls and honest limits |
| Negative result and full project abandonment | Not selected as the sole artifact | A reusable product gap was not demonstrated, but learning material, evidence discipline and local regression recipes have concrete retained value |

Native buffering and the final epoch-validation recipe suffice for the declared
waiting/held-work contract. The evidence gives no reason to develop another
buffer framework, client SDK, runtime watchdog service or dashboard. The PIVOT
from Milestone 1.7 is preserved.

## Completion state and reopening conditions

Original Stages 0–7 have research outputs and reviewed exit criteria, with their
explicit scopes in [final compliance](FINAL_PRD_COMPLIANCE.md). The bounded
research process and owner handover are complete. Broader technical portability,
physical-camera validation, external RTSP and adoption gates are incomplete.
Package acceptance/release is not achieved. Overall classification:
**RESEARCH COMPLETE WITH EXPLICIT UNMET EXTERNAL GATES**.

Reopen only for a separately authorized, bounded question supported by new input:

1. An independent application with a reproducible supported-behavior defect and
   native controls already evaluated fairly.
2. A precise integration whose total necessary instrumentation is small and whose
   evidence improves on an application-specific pytest/FFmpeg recipe.
3. A reviewed compatible external RTSP environment or a source with substantiated
   capture identity/clock semantics, plus explicit real-camera authorization.
4. Actual Windows execution and a proportionate compatibility plan if that target
   is pursued.
5. Genuine maintainer acknowledgment, two unrelated interested developers and
   owner-approved license/publication policy before package productization.

No follow-on milestone, upstream posting, publication or deployment starts
as part of this handover.

## Subsequent source-release preparation — 23 October 2026

The research findings and unmet adoption/package gates above remain unchanged.
The owner subsequently authorized security review, conditional MIT licensing and
conditional public publication of this source repository. That authorization
is not ownership evidence or package-release approval. Current gate results are
recorded in the [release-readiness report](../release/PUBLIC_RELEASE_READINESS.md).
The two original PRDs remain private local inputs and are excluded from Git.

### MIT source-publication authorization — 24 October 2026

The owner explicitly confirmed ownership/necessary rights, approved MIT with
`Copyright (c) 2026 devAIsh88`, and accepted disclosure of the existing Git author
email and historical checkout path. The original repository material is now
[MIT licensed](../../LICENSE); the earlier pending-license rows are historical.
Publication of this original repository is authorized after final security and
private CI verification. This resolves the source-license/public-visibility
approval gate, without resolving adoption or approving a package/deployment.
The original PRDs remain unchanged, untracked and excluded. See the
[current release record](../release/PUBLIC_RELEASE_READINESS.md).
