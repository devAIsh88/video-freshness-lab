# Contributing

The research outcome is a reference recipe and reliability validation toolkit.
Prefer small fixes, clearer diagnostics and reproducible evidence. A new streaming
framework or package is outside the accepted scope. Read the [walkthrough](docs/guides/PROJECT_WALKTHROUGH.md),
[evidence contract](docs/architecture/frame-evidence-contract.md) and
[final decision](docs/audits/FINAL_GO_NO_GO_DECISION.md) before proposing behavior changes.

Licensing remains pending explicit ownership confirmation. Do not incorporate
external contributions or third-party code until redistribution rights are clear.
See [release readiness](docs/release/PUBLIC_RELEASE_READINESS.md). The original
PRDs are private local inputs, deliberately absent from Git; requirement-dependent
implementation needs owner-provided copies. Routine bug fixes can be reviewed
against the published contracts and tests.

## Local setup and verification

Use Python 3.11+ and the [README installation commands](README.md#install-and-run-the-python-core).
Install editable with the `dev` extra, then run from the checkout root:

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

Keep the core free of runtime dependencies. Record purpose, version, license,
source and alternatives before adopting a dependency. The
[dependency review](docs/release/THIRD_PARTY_LICENSE_REVIEW.md) distinguishes
development tools, optional images, system media libraries and the disposable
external audit. Optional integration commands are in the [runbook](docs/guides/DEMO_RUNBOOK.md).

## Tests and evidence

Use synthetic inputs, controlled events and injected clocks. Cover observable
contracts, invalid inputs and failure cases. Separate no arrival, repeated content,
queued old frames and obsolete-epoch completions. Report unknown evidence, cleanup
failures and initial failures honestly; do not retry silently until green.

Keep GStreamer/OpenCV tests separate from ordinary Python CI. Use only owned
loopback sockets and bounded trials, with positive process/thread/pipeline cleanup.
Do not infer physical-camera freshness from local receipt time or decoder PTS.

## Review and Git

Describe the concrete problem, resulting behavior, actual checks and limitations.
Use one coherent conventional commit per meaningful change. Never force-push or
rewrite history. Review full diffs and explicitly stage intended paths; do not
use `git add .`. Check ignored paths and document containers as well as text.

Exclude credentials, original PRDs, private connection data, recordings, environments,
caches and generated binaries. Follow [SECURITY.md](SECURITY.md) for sensitive findings.
CI uses pinned actions, read-only permissions and bounded jobs. No deployment,
package publishing, releases or paid services are part of this project.
