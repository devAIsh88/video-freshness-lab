# Start here: understand the lab in 75 minutes

Video Freshness Lab asks whether a successful video read is enough to trust the
result produced from it. It is an MIT-licensed research repository and reference
recipe, with optional local media experiments. The final decision is **PIVOT to
native buffering plus explicit application evidence and a final epoch check**.
A production framework or public package is not approved.

Use the existing Fedora environments. No real camera is needed. Run commands
from the repository root. Keep the two owner-provided PRDs local and untracked.
The [demo runbook](DEMO_RUNBOOK.md) contains prerequisite checks and exact commands.

## A practical learning sequence

| Minutes | Read / run | What you should be able to explain afterward |
| --- | --- | --- |
| 0–10 | README and the first half of [walkthrough](PROJECT_WALKTHROUGH.md) | Availability, delivery, identity progress and final result freshness are different |
| 10–20 | Run the simulator and threaded normal/slow demos from the runbook | Why FIFO accumulates old work and a latest mailbox replaces waiting work |
| 20–30 | Walkthrough's epoch example; read SessionPipeline.complete in the [code guide](CODEBASE_GUIDE.md) | Why a result already being processed can survive a reconnect; where validation must occur |
| 30–40 | Read the evidence section; run the focused session/evidence tests | Why local arrival, decoder PTS and physical capture time cannot be substituted for each other |
| 40–50 | Run stamped images; inspect [image results](../experiments/stamped-images-results.md) | Marker identity is created at the source and verified after the selected transformation |
| 50–60 | Run the small GStreamer and RTSP demonstrations if prerequisites pass | Native queues handle waiting buffers; the final application check handles held results |
| 60–70 | Read [independent audit](../audits/THIRD_PARTY_CONSUMER_AUDIT.md) and [decision](../audits/FINAL_GO_NO_GO_DECISION.md) | Supported external behavior was tested; no reusable freshness defect or adoption demand was invented |
| 70–75 | Rehearse the 90-second explanation and five difficult questions in [Q&A](PROJECT_EXPLANATION_QA.md) | State the contribution, results and limits without overclaiming |

For a 60-minute session, read the GStreamer/RTSP observations instead of running
both suites. For 90 minutes, inspect one test beside each corresponding method
and run the complete 305-test Python suite.

## What to remember for a demonstration

1. Show ordinary successful processing alongside old FIFO evidence.
2. Explain that latest-frame buffering replaces only waiting items.
3. Hold an old result across an epoch transition; check it at publication.
4. Show the original marker surviving an image transformation, and UNKNOWN when
   a crop removes it.
5. State which results are simulation, threads, native GStreamer, local RTSP and
   external consumer evidence. Never combine their trial counts into one rate.
6. Finish with the research decision: keep the recipe/toolkit; defer package work.

The strongest concise statement is: “We demonstrated and tested the boundary
between receiving a frame and publishing a result from valid evidence. Native
GStreamer buffering was sufficient for waiting work, so we kept only the small
application policy that native queues cannot apply to already acquired work.”

## Documents to consult rather than memorize

- [Codebase guide](CODEBASE_GUIDE.md): actual modules, classes, synchronization and tests.
- [Demo runbook](DEMO_RUNBOOK.md): commands, expected observations, cleanup.
- [Final research report](../experiments/FINAL_RESEARCH_REPORT.md): evidence by environment.
- [Final compliance audit](../audits/FINAL_PRD_COMPLIANCE.md): every stage and unmet gate.
- [Original technical completion report](../audits/TECHNICAL_STAGE_COMPLETION_REPORT.md): Stage 0–5 history and exact earlier commits.

The PRD stages 0–7 describe research obligations. Implementation milestones
1.1–1.9 are development increments; their numbers do not map one to one.
