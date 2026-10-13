# Contributing

Read both PRDs, [scope decisions](docs/architecture/foundation.md), and the
[validation plan](docs/experiments/validation-plan.md) before changing behavior.
Licensing is pending; agree redistribution terms with the owner before accepting
external contributions or copying third-party code.

## Local setup

Use Python 3.11+ and follow the [README installation commands](README.md#install-and-check).
Install editable with the `dev` extra, then run:

```sh
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Keep runtime dependencies empty for this milestone. Direct development and build
dependencies and their license/source are recorded in the architecture document.
Record purpose, version, source, license, and alternatives before adding another.

## Tests and evidence

The import test checks the installed distribution and this checkout's `src`
package without injecting a test-only import path. Future behavior tests must
cover observable contracts, invalid inputs, and failure cases. Use synthetic
inputs, controlled event order, and injected clocks rather than timing sleeps.
Report cleanup, unexplained flakiness, and negative findings. Never retry silently
until a scenario passes or infer external reliability from an intentionally
broken demonstration. Transport tests belong to later PRD stages.

## Review and Git

Keep each pull request within its approved milestone. Describe the problem,
behavior changed, test commands and actual results, limitations, and PRD gates.
Review generated code and documentation line by line. Include no secrets, media,
private paths, or unverified claims. CI must pass before acceptance.

Use imperative conventional commits: `chore:`, `docs:`, `test:`, `feat:`, or
`fix:` as appropriate. Prefer one coherent commit per completed milestone;
do not manufacture activity or combine unrelated stages. Milestone 1.1 proposes
`chore: establish validation harness foundation` only after checks pass and the
owner approves the complete staged contents. Never force-push or rewrite history.

Before staging, inspect `git status --short --ignored`, candidate paths, file
sizes, and contents; scan text and document containers for secrets. Stage an
explicit reviewed file list. Inspect `git diff --cached --name-status`,
`git diff --cached --stat`, `git diff --cached --check`, and the complete
`git diff --cached`. Ignore rules are a guardrail, not a secret scanner.
Only the owner can authorize repository creation, pushing, public visibility,
licensing, deployment, or publishing. Current policy permits CI only.
