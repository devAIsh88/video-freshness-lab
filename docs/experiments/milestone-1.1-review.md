# Milestone 1.1 owner review

Foundation local validation has passed on Fedora Linux 44 with Python 3.12.15.
The staged foundation is ready for owner review and first local commit approval.
PRD publication clearance, license selection, and public release remain pending.
No Milestone 1.2 behavior was implemented. No commit, remote, push, deployment,
or publication was performed.

## Requirements understanding

The PRDs select a staged synthetic learning lab, not a production RTSP framework.
Availability, delivery, liveness, frame freshness, and result freshness are
distinct observations. The project must earn any standalone-package scope with
deterministic tests, independent consumer evidence, small instrumentation burden,
and external interest. A recipe, upstream contribution, or closure is valid.

The current owner instruction narrows the PRDs' full Stage 1 to scaffolding.
Specific session boundaries, evidence provenance, freshness thresholds, library
guarantee overlap, and market demand remain unverified. Fedora/Windows targets
and stronger adoption gates come from the more detailed DOCX. See the
[foundation decisions](../architecture/foundation.md) and
[investigation plan](validation-plan.md) for definitions and open questions.

## Files and dependencies

Created: `pyproject.toml`, `src/video_freshness_lab/__init__.py`,
`tests/test_package_import.py`, `.github/workflows/ci.yml`, `.gitignore`,
`.env.example`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `AGENTS.md`,
`LICENSE` (pending decision), `docs/prd/README.md`,
`docs/architecture/foundation.md`, `docs/experiments/validation-plan.md`,
and this report. Existing PRDs were not edited or relocated.

No runtime dependencies. Direct development tools: pytest 8.4.2 for tests and
Ruff 0.14.0 for lint/format. Build tool: setuptools 80.9.0 for editable packaging.
Sources/licenses are recorded in the architecture document. Transitives are not
locked; later experiment evidence must record resolved versions.

## Actual local validation

Current environment: Fedora Linux 44, `.venv` Python 3.12.15, pip 26.2.1,
pytest 8.4.2, Ruff 0.14.0. The owner installed dependencies before this review.
The virtual environment is isolated and its editable metadata points to this
checkout; package imports resolve to `src/video_freshness_lab/__init__.py`.
Installation was verified from the existing environment, not rerun in this review.

| Check | Result |
| --- | --- |
| `.venv/bin/python -m ruff check .` | Exit 0: all checks passed |
| `.venv/bin/python -m ruff format --check .` | Exit 0: 2 files already formatted |
| `.venv/bin/python -m pytest -v` | Exit 0: 1 package-import smoke test passed |
| `.venv/bin/python -m pip check` | Exit 0: no broken requirements |
| Virtual environment and editable metadata/origin check | PASS on Python 3.12.15 |
| CI YAML and expected workflow structure | PASS static inspection; no deployment/publishing |
| Original PRD SHA-256 comparison | PASS; both originals unchanged and untracked |
| Sensitive-path ignore probes | PASS, including explicit repository rules for both environment directories |
| Targeted text and DOCX XML secret/address scan | Zero matches; limited heuristic scan, not exhaustive assurance |
| `git diff --cached --check` | Exit 0: no staged whitespace errors |

PyYAML was used from the host for static inspection only; it was not added as a
project dependency. GitHub Actions has not executed, and actionlint was not run.
The single smoke test validates packaging; it does not validate stream behavior,
prove the central hypothesis, or complete the PRDs' full Stage 1 learning lab.
Windows and Python 3.11 execution remain unverified locally.

Commands actually run from this checkout:

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --cached --check
git status --short
```

Resolved test-tool versions match the project pins. Installed test dependencies
are pluggy 1.6.0, iniconfig 2.3.1, packaging 26.3, and Pygments 2.21.0.
Setuptools is absent from the runtime environment, which does not invalidate an
editable installation built in isolation; its declared build pin remains 80.9.0.
The original DNS-blocked attempts are preserved below as history, not current
test results. Owner approval is still required before any commit.

Final review changes: added `.venv-backup/` to the repository ignore rules rather
than relying on the backup's internal `.gitignore`, documented Python 3.12 setup
and verified Fedora status in README, and updated this report. No implementation
or dependency versions changed. The complete staged content and these changes
were reviewed; both PRDs remain outside the index pending publication clearance.

## Historical environment recovery verification

This section records earlier failed attempts on Python 3.14.7. The current Fedora
Python 3.12 verification above supersedes its blockers and commit recommendation.

A follow-up diagnosis reproduced the blocker without changing project dependency
versions or making persistent network changes:

- System and virtual-environment Python are both 3.14.7; virtual-environment pip
  is 26.0.1. The interpreter and pip run, isolation is intact, and `pip check`
  reports no broken installed requirements. This does not establish that the
  project is installed; setuptools, pytest, and Ruff remain absent.
- DNS resolution for both `pypi.org` and `files.pythonhosted.org` fails with
  `socket.gaierror`, errno -3 (`EAI_AGAIN`). Verified HTTPS probes fail at the
  same resolution step, before TCP connection or TLS negotiation.
- The executor reports a network-disabled sandbox. No proxy variables, package
  index overrides, trusted-host settings, or existing pip configuration files
  were found. The apparent pip `:env:` entry is not an index/proxy setting.
  This points to restricted execution-environment connectivity rather than a
  dependency-version or project configuration error. TLS health could not be
  assessed because the handshake was never reached; no proxy failure was observed.
- No managed network policy snapshot or environment-status tool was available.
  The runtime skill was read for diagnosis; no managed network setting was changed.
- Standard pip/uv caches, uv's user-managed Python location, and inspected
  temporary cache locations were absent. The system has pip and uv but no
  setuptools, pytest, Ruff, or actionlint. No offline installation source was
  found. The pip cache-permission warning is secondary to unavailable package
  access; disabling pip's cache for the retry did not recover installation.

The bounded retry was:

```sh
PIP_RETRIES=0 PIP_TIMEOUT=10 .venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir -e ".[dev]"
```

It exited 1 while installing isolated build dependencies: setuptools 80.9.0
could not be fetched. Pip's "No matching distribution found" message is not
evidence that the pinned version is invalid when the index is unreachable.

The complete requested follow-up validation was attempted:

| Command | Result |
| --- | --- |
| `.venv/bin/python -m ruff check .` | Exit 1: no module named ruff; lint did not execute |
| `.venv/bin/python -m ruff format --check .` | Exit 1: no module named ruff; formatting check did not execute |
| `.venv/bin/python -m pytest -v` | Exit 1: no module named pytest; no tests collected or executed |
| `git diff --cached --check` | Exit 0: no staged whitespace errors |
| `git status --short` | Exit 0: 15 foundation files staged; both original PRDs untracked |

All staged files were inspected again, their contents matched the working tree,
and the limited secret/address scan found no matches. Original PRD hashes still
match. Static CI inspection confirms installation plus lint/format/test steps
only; no deployment or publishing workflow exists. README claims match the
docstring-only package and smoke-test source. No code/configuration defect was
established by these inspections; real lint and test results remain unavailable.
Only this review report changed during recovery.

Remaining safe recovery options are to run these same checks in an approved
executor with PyPI connectivity, or obtain a trusted local wheelhouse containing
the existing pinned tools and all resolved build/test dependencies compatible
with the selected Python/platform. Neither option was available here. For a
prepared wheelhouse, a process-local offline installation command is:

```sh
PIP_NO_INDEX=1 PIP_FIND_LINKS=/path/to/trusted/wheelhouse .venv/bin/python -m pip install -e ".[dev]"
```

This command is an option, not an executed recovery. It must also satisfy the
isolated build environment. Do not disable TLS verification, substitute an
untrusted mirror, change pins to mask connectivity, or bypass sandbox policy.
Recommendation: Milestone 1.1 is not ready to commit until editable installation,
Ruff checks, and pytest pass and the owner approves the final staged contents.
PRD publication clearance and licensing remain pending; no commit, push,
publication, or Milestone 1.2 work was performed.

## Security and publication observations

Only expected source/docs and the original DOCX were found. Largest input:
the original 52,679-byte DOCX. No recordings, datasets, credentials, or unexpected
binaries were present. DOCX inspection found empty author/modifier fields, no
external relationships or embedded objects, and a blank thumbnail. A named
third-party project reference remains in its privacy section; the owner must
confirm whether the originals may be published and that redistribution rights
are held. They remain intact and unstaged pending that decision.

Foundation text has no private-address or credential matches in the targeted
scan. `.env.example` contains comments only. Ignore probes cover environment
files, environments, keys, editor state, recordings, snapshots, local test data,
and packet captures. CI has read-only permissions, pinned actions, no persisted
checkout token, ordinary PR/main triggers, and a ten-minute timeout. No paid
service or deployment infrastructure is needed. License selection and a verified
private vulnerability-reporting channel remain owner decisions before release.

## Git and pending owner actions

Git was initially absent in this project directory and was initialized on `main`.
No existing history was rewritten. Reviewed foundation files are staged with an
explicit list; originals remain untracked and `.venv` is ignored. The complete
staged text diff must be approved after successful checks. Proposed sole commit:
`chore: establish validation harness foundation`.

Suggested repository name: `video-freshness-lab` (availability under the owner's
GitHub account has not been checked). Description: "Synthetic experiments and
deterministic tests for video freshness and stream session boundaries."
GitHub CLI is not installed on this host. The following commands are prepared
for later use after installing/authenticating `gh`; none was executed.

Only after checks pass, publication rights are confirmed, and the owner approves
the resulting staged contents, include the original documents and review again:

```sh
git add -- PRD.md Video_Freshness_Lab_PRD_v0.1.docx
git status --short --ignored
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git diff --cached
# Review DOCX content/metadata separately; Git displays it as a binary.
git commit -m "chore: establish validation harness foundation"
```

Repository creation and pushing require separate explicit owner approval.
These commands create a private remote; public visibility requires another
explicit decision after licensing and disclosure clearance:

```sh
gh auth login
gh repo create video-freshness-lab --private --source=. --remote=origin --description "Synthetic experiments and deterministic tests for video freshness and stream session boundaries."
git push -u origin main
```

Run from this project directory. If the name is taken or `origin` already exists,
stop and inspect rather than overwriting a remote. Follow the official
[repository creation](https://cli.github.com/manual/gh_repo_create) and
[authentication](https://cli.github.com/manual/gh_auth_login) command references.

## Next milestone proposal

Milestone 1.2: deterministic in-process stream-failure simulation with numbered
items, FIFO/latest-item controls, pure lag/age metrics, and controlled slowdown
and no-progress tests. Epoch contracts and realistic RTSP faults retain their
later PRD stages unless explicitly revised. This work has not begun.
