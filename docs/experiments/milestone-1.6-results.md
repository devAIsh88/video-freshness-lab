# Milestone 1.6: frame evidence and existing-library baseline

## Scope and method

This owner-authorized milestone follows 1.5 commit
`f30d70865de1e63fbade7d1e8b911a9de5760f44`. It implements a frozen, typed
evidence sidecar and one pure diagnostic, with no transport or media pipeline.
Both original PRDs were read, including all DOCX paragraphs; their contents remain
unchanged and untracked. The existing validation plan and historical milestone
reports retain their scope and limitations. No completed milestone was amended.

See the [formal contract](../architecture/frame-evidence-contract.md) and
[official-library capability matrix](../research/existing-library-capability-matrix.md).
The matrix distinguishes documented capability, verified local inspection,
hypothesis, and unknown/requires experiment. Sources were accessed 2026-10-20.

Local execution: Fedora Linux 44, Python 3.12.15, pytest 8.4.2, Ruff 0.14.0.
No runtime or development dependency was added or changed. Editable installation
was rebuilt with `.venv/bin/python -m pip install -e ".[dev]"`. The first attempt
failed because sandbox DNS could not reach PyPI during isolated setuptools setup;
the approved network-enabled rerun succeeded. A server restart interrupted the
earlier rerun's output; its outcome was not assumed. The completed rerun built and
installed the editable wheel successfully. pip's sandbox cache warning was
nonfatal; no administrator action or system package modification was used.

## Deterministic observations

All values in this table are injected nanoseconds, not performance measurements.
The baseline is source `synthetic-source`, epoch 0, sequence 1, controlled capture
10, local arrival 20, evaluation 30, age budget 20. PTS is separate metadata even
when the fixture assigns equal values. Session and age are independent axes;
there is no combined pass/fail or admission decision.

| Fixture | Established observation | Limitation / unknown |
| --- | --- | --- |
| Ordered epoch/PTS, exact rescaling | Current session; capture age 20, `fresh`; evaluating at 31 gives age 21, `stale` | Verified capture reference is controlled synthetic ground truth only |
| Missing PTS and capture | Current session; capture age `None`, `unknown`; missing fields reported | No zero-latency substitution |
| Arrival only | At 30, arrival age 10 is `fresh`; at 41, age 21 is `stale` | Capture freshness remains `unknown` in both cases |
| Identical symbolic pixels, different arrivals | Same pattern label; arrival ages 10 and 5; ordinals advance | Neither new exposure nor freeze is established |
| Reset at reconnect | Epoch 1 sequence 0/PTS 0 follows epoch 0 sequence 10/PTS 1000 without cross-epoch regression findings | Controller supplies the boundary; real restart detection is untested |
| Reset without boundary | Same-session nonadvancing ordinal and regressing PTS reported | Not attributed to a decoder defect |
| Source or epoch mismatch | `obsolete_session` independently of measured stale age | Does not infer physical camera identity |
| Missing, zero, negative time bases | Capture `unknown`; missing/invalid base codes | A raw zero denominator must become unavailable before Fraction construction |
| Reported capture, missing provenance, or other clock domain | Age `None`, `unknown` | PTS/decoder reputation cannot substantiate capture semantics |
| PTS 0 to 50, gap budget 49 / 50 | Discontinuity reported only for strict budget excess | No default frame-rate assumption; signed/equal PTS alone is not a defect |
| Changed PTS domain or identity kind | Incomparable PTS; no subtraction of unlike ordinal kinds | Origin mapping and continuity require external evidence |
| Impossible timing | Future capture, capture after arrival, or arrival after evaluation yields unknown age | Invalid ordering is not a stale observation |
| Old result after 1.5 transition | Original accepted frame remains traceable; final completion is obsolete, output ledger empty | Capture freshness remains unknown; no new sink or epoch lock added |
| Missing source/provenance | Session unknown and diagnostic issues, independently of known fixture age | A measured age is not overall validity |

Focused tests also reject malformed structural inputs and mutable metadata, and
preserve frozen historical admission facts when a later boundary records rejection.
The compatibility fixture copies only the original frame's epoch and sequence;
it does not relabel `produced_at_ms` as physical capture time.

## Actual library findings

**Verified locally:** read-only `gst-inspect-1.0 --version` and plugin inspection
report GStreamer/appsink 1.28.6. appsrc/appsink/videotestsrc are inspectable.
appsink lists bounded/leaky controls, queue-level properties, and input/output/drop
counters. `ffmpeg -version` and `ffprobe -version` report 8.1.2. `find_spec`
reports no `av`, `cv2`, or `gi` in the project venv. These observations establish
availability of installed tools/properties only, not working media behavior.

**Documented:** GStreamer offers native queue/drop mechanisms; FFmpeg exposes
timestamp and protocol-specific buffering controls; PyAV exposes packet/frame
timestamps; OpenCV exposes selected backend-specific timing and timeout fields.
The [matrix](../research/existing-library-capability-matrix.md) supplies the exact
versions, official links, scope, and unresolved questions. Old PyAV stable URLs
and version-specific FFmpeg fetch failures are recorded rather than silently
treated as current guarantees.

**Hypothesis:** native GStreamer queue configuration plus a small application
final-output check could make a separate mailbox/package unnecessary.
**Unknown:** actual buffer accounting, metadata preservation, blocked-read cleanup,
reconnect behavior, physical source identity, capture clock trust, and equivalent
final-output semantics in an independent consumer. No external defect, package
gap, commercial demand, or adoption interest was established.

## Validation and reproducibility

```sh
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest tests/test_evidence.py -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
.venv/bin/python -m video_freshness_lab --suite all --json
.venv/bin/python -m video_freshness_lab.threaded_demo --mode slow --items 10 --json
```

The focused suite passes **19 test cases**. The full suite passes **259 tests**,
including all **240 previous tests**. Ruff lint and formatting (22 Python files),
pip dependency integrity, and working/staged whitespace checks pass. Editable
package import resolves this checkout; the new evidence module imports normally.
The existing simulator CLI returns valid JSON for all 13 scenarios; the existing
threaded CLI returns valid JSON. CLI/import tests also remain in the full suite.
Fixtures use no sleeps, real clocks, images, network capture, or new threads.
The previous thread lifecycle tests and leak guard remain active.

No additional 100-run integration reliability claim is made: these pure fixtures
are not an independent library experiment. Local execution is Python 3.12 only;
Ubuntu Python 3.11/3.12 is checked by existing CI after delivery. Windows remains
unverified. Delivery SHA, remote verification, and CI outcome are reported after
the one milestone commit, without a second status-only commit.

## Security and delivery review

Only source, synthetic tests, sanitized documentation, and current scope/index
updates are selected for staging. No dependencies, CI permissions, license,
deployment, paid infrastructure, or publication settings are changed. Both PRD
hashes are checked against their prework values, and both files are checked absent
from tracked/staged files and all Git history. Document-container members,
tracked/staged text, and history blobs are reviewed for prohibited data using a
local heuristic scan; this is not a guarantee that every possible secret can be
detected. Ignored environments, caches, packaging metadata, and local tool/account
directories are inventoried and excluded; credential files are not displayed.

Only the intended private remote may receive the verified commit. Foundation
history must remain intact. No force push or amendment is permitted. GitHub
identity, ownership, visibility, remote branch, and CI outcomes must be verified
at delivery; failed synchronization is reported as PUSH PENDING. Owner Actions
spending controls remain required; this milestone does not enable paid usage.

## Recommendation and stop

Authorize the [proposed finite GStreamer 1.28.6 appsrc/appsink comparison](../research/existing-library-capability-matrix.md#first-evaluation-recommendation-proposal-not-executed)
before any RTSP adapter. Compare native bounded/leaky configuration against that
same configuration plus a final-output epoch check, with identical inputs and
ordered gates. Exact local binding/dependency choices and their licenses need
review before adoption. No privileged system modifications are proposed.

Build only a small adapter/test if observable independent behavior demonstrates
added value with precise, low-burden lineage. Pivot to native configuration docs,
a recipe, or an upstream regression test if existing mechanisms suffice. Stop
capture-freshness claims when ground truth or clock mapping is absent; simplify
or stop if only contrived demos fail or reproducibility remains poor. The full
PRD external, reliability, adapter-size/value, maintainer/adoption, and maintenance
gates remain open. Licensing and public disclosure remain owner decisions.

Milestone 1.6 ends here. Real media pipelines, stamped-image lineage, RTSP,
third-party behavioral audits, and productization require new authorization.
