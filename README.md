# Video Freshness Lab

Milestone 1.6: frame evidence diagnostics and existing-library capability research.
This research lab implements a virtual clock, FIFO/latest-frame waiting buffers,
one simulated consumer, session/fault scripts, optional session filtering,
no-progress detection, explicit metrics, structured evidence, and a small CLI.
A separate real-thread demo uses a bounded latest-frame mailbox with explicit
drain-on-close behavior and bounded joins.
No RTSP capture, decoding, images, or production reliability API is implemented.

## Problem and research status

A successful frame read or a live process does not by itself establish the age
or source session of the evidence behind an application output. The hypothesis
is that backlog or reconnection can allow stale frames or previous-session
results to escape otherwise healthy consumers. We have not reproduced this in
an external consumer, established a market gap, or shown that a separate package
adds value over existing libraries.

The [Markdown PRD](PRD.md) and [full DOCX PRD](Video_Freshness_Lab_PRD_v0.1.docx)
remain unchanged at their original paths. See the [source index](docs/prd/README.md),
[scope decisions](docs/architecture/foundation.md), and
[validation plan](docs/experiments/validation-plan.md). The PRDs' full Stage 1
learning lab is broader than this in-process milestone and remains unfinished.
The original PRDs are local, untracked source documents and are intentionally
absent from GitHub clones. Consult the owner's local copies before new
implementation; their linked paths resolve only where those copies are present.

Run `.venv/bin/python -m video_freshness_lab` for all four buffering scenarios,
or add `--json` for complete machine-readable evidence. Use `--help` for integer
millisecond configuration overrides. See [simulation architecture and metrics](docs/architecture/simulation.md)
and [measured Milestone 1.2 results](docs/experiments/milestone-1.2-results.md).
Slow FIFO keeps all 10 frames but reaches 310 ms result age; under the identical
workload latest-frame drops six waiting frames and reaches 70 ms. Neither result
establishes how a real camera reader behaves.

Run `.venv/bin/python -m video_freshness_lab --suite recovery` for nine interruption
presets. Add `--policy latest --session-filter` to compare waiting-frame replacement
with provenance checks. [Milestone 1.3 results](docs/experiments/milestone-1.3-results.md)
document configurations and limits: latest-frame alone emits two obsolete-session
results in the reconnect script despite passing its age budget; adding session
checks suppresses them in this synthetic model. The same result does not establish
any real RTSP library defect.

Run `.venv/bin/python -m video_freshness_lab.threaded_demo --mode normal` for
the producer/consumer handoff, `--mode slow` for controlled replacement, or
`--mode idle` for shutdown of an empty blocked consumer. Add `--json` for counts,
frame metadata, and final state. With ten items, normal delivers ten; slow
delivers the first and last while replacing eight waiting items. These counts
follow explicit thread coordination, not a scheduling or throughput benchmark.
See the [mailbox contract](docs/architecture/threaded-mailbox.md) and
[Milestone 1.4 results](docs/experiments/milestone-1.4-results.md).

The session experiment checks provenance again at final publication, with epoch
validation and output recording under one lock. A result from an in-progress
retired epoch can finish internally and be suppressed. Source closure retains
drain-on-close; application shutdown separately suppresses subsequent outputs.
Run `.venv/bin/python -m pytest tests/test_threaded_sessions.py -v` to reproduce
the synchronized scenarios. See the [session boundary contract](docs/architecture/threaded-session-boundaries.md)
and [Milestone 1.5 results](docs/experiments/milestone-1.5-results.md). These tests
do not validate real RTSP behavior or establish an age-based freshness policy.

Milestone 1.6 adds a [frame evidence contract](docs/architecture/frame-evidence-contract.md)
and pure diagnostics that separate session validity, arrival age, and substantiated
capture age. Missing or incomparable capture references remain unknown. The
[official-library comparison](docs/research/existing-library-capability-matrix.md)
recommends testing native GStreamer queue policies before building another
mechanism. See [1.6 fixtures and limitations](docs/experiments/milestone-1.6-results.md).
No media pipeline, transport adapter, or new runtime dependency is introduced.

## Install and check

Use Python 3.11 or newer; Fedora development uses Python 3.12. From this directory:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

On Windows PowerShell, create the environment with `py -3.11 -m venv .venv`
and use `.venv\Scripts\python.exe` in place of `python`; activation is optional.
Run `python -m ruff format .` to apply formatting. No camera, environment
variables, network stream, GPU, or paid service is needed. Initial dependency
installation requires access to PyPI or an approved local wheel source.

CI runs the same installation and checks on Ubuntu with Python 3.11 and 3.12.
Local foundation checks have passed on Fedora with Python 3.12. Windows remains
an unverified PRD portability target; neither platform is in the initial CI matrix.
Development tool versions are pinned; transitive dependencies are not locked,
so this is not a fully reproducible dependency snapshot. Record resolved
versions with `python -m pip freeze` when collecting experiment evidence.

## Scope and uncertainty

Current work uses numbered synthetic items and controlled event order.
Transport comes only after pure contracts have been validated. Sequence lag
measures distance from the source head; evidence age measures elapsed time;
neither a nominal frame rate nor connection status substitutes for these.
The simulator defines explicit synthetic thresholds and session boundaries;
source lineage across transport and real reconnect/session semantics remain
unverified investigation questions.

Non-goals are a capture SDK, RTSP server, NVR, dashboard, AI detection or model
training, hosted service, safety certification, and deployment infrastructure.
CI performs checks only: no publishing, releases, containers, cloud credentials,
or deployment. Synthetic data is mandatory during validation. Verified milestone
commits may synchronize to the owner-approved PRIVATE GitHub repository; public
visibility and releases remain unapproved. See AGENTS.md for delivery requirements.

The package name `video_freshness_lab` and distribution name
`video-freshness-lab` are provisional local choices; global availability has not
been checked. Version `0.0.0` identifies scaffolding, not a release. Licensing is
[pending owner approval](LICENSE), so this is not yet a licensed open-source
release. See [contributing](CONTRIBUTING.md) and [security](SECURITY.md).
