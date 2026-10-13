# Video Freshness Lab

Milestone 1.2: deterministic buffering experiments on numbered synthetic frames.
This research lab implements a virtual clock, FIFO/latest-frame waiting buffers,
one simulated consumer, explicit metrics, structured evidence, and a small CLI.
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

Run `.venv/bin/python -m video_freshness_lab` for all four buffering scenarios,
or add `--json` for complete machine-readable evidence. Use `--help` for integer
millisecond configuration overrides. See [simulation architecture and metrics](docs/architecture/simulation.md)
and [measured Milestone 1.2 results](docs/experiments/milestone-1.2-results.md).
Slow FIFO keeps all 10 frames but reaches 310 ms result age; under the identical
workload latest-frame drops six waiting frames and reaches 70 ms. Neither result
establishes how a real camera reader behaves.

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
Freshness thresholds, source lineage across transport, and reconnect/session
semantics remain proposed investigation decisions.

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
