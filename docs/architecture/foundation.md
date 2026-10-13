# Foundation scope and decisions

## Authority and confirmed objectives

Read both [source PRDs](../prd/README.md). Their confirmed direction is Video
Freshness Lab: teach buffering and evidence freshness, establish deterministic
contracts, reuse transport tools, then audit third-party behavior before deciding
whether to package anything. CPU-only synthetic validation, Python 3.11+, minimal
dependencies, CI only, privacy, and honest negative results are constraints.

Milestone 1.1 adds repository scaffolding only. The conceptual later flow is
controlled source → application under test → evidence adapter → oracle → report,
with an optional fault controller. None of these components is implemented yet.
The installed package contains only a docstring; it creates no threads, opens no
connections, reads no environment variables, and exports no pretend functionality.

## Differences and unresolved decisions

- The owner's current milestone subdivides the PRDs' broad Stage 1. Its explicit
  foundation-only scope takes precedence. FIFO/latest-item examples remain future
  work; full Stage 1 and later session/transport gates remain unmet.
- The PRDs describe stale-result behavior as established; this repository has
  not independently reproduced it. Specific reconnect leakage, library defaults,
  contract sufficiency, and package demand remain hypotheses for investigation.
- The DOCX specifies Fedora/Windows portability targets, Ubuntu Python 3.11/3.12
  CI, a roughly 30-line adapter, and detailed adoption gates. The shorter Markdown
  omits some detail rather than explicitly rejecting those constraints.
- Proposed disconnect/reconnect epochs are test conventions, not proof that a
  transport reconnect creates a new physical source session. Boundary detection,
  timestamp provenance, grace budgets, and output lineage require later evidence.
- The next requested milestone is deterministic stream-failure simulation. Start
  with numbered items under the PRDs' Stage 1; do not pull forward Stage 4 transport
  faults or Stage 2 production oracle scope without an explicit scope decision.
- Licensing, copyright owner, publication rights, private vulnerability contact,
  external audit target, RTSP source, and plugin-versus-recipe outcome are pending.

## Packaging and tooling

`video_freshness_lab` is a provisional import name derived from the PRD title;
`video-freshness-lab` is the local distribution name. Neither is asserted globally
unique or reserved. A `src` layout and editable install make missing installation
visible. The smoke test verifies distribution metadata and the checkout's package
origin; no pytest `pythonpath` shortcut masks packaging problems.

There are no runtime dependencies. Direct tooling is pinned for consistent local
and CI commands; transitive dependencies and Python patch versions are not locked.
Review pins deliberately when updating, and record full resolved environments
for later experiments. Tool license references are not this repository's license.

| Dependency | Version | Role | Source / license |
| --- | --- | --- | --- |
| setuptools | 80.9.0 | PEP 517/660 build and editable installation | [PyPI](https://pypi.org/project/setuptools/80.9.0/) / MIT |
| pytest | 8.4.2 | Development smoke test and future contracts | [PyPI](https://pypi.org/project/pytest/8.4.2/) / MIT |
| Ruff | 0.14.0 | Development lint and formatting checks | [PyPI](https://pypi.org/project/ruff/0.14.0/) / MIT |

## CI and security choices

Use the DOCX's two-version Ubuntu matrix, a ten-minute timeout, read-only contents
permissions, ordinary pull requests and main pushes, and no persisted checkout
credentials. No deploy, release, artifact upload, secrets, or publishing steps.
Official release commits were checked against the
[checkout v4.2.2 release](https://github.com/actions/checkout/releases/tag/v4.2.2)
and [setup-python v5.6.0 release](https://github.com/actions/setup-python/releases/tag/v5.6.0).

Ignore local media broadly until a reviewed small synthetic fixture justifies a
narrow exception. `.env.example` contains comments only because no configuration
is needed. Ignore rules do not replace staged-content review or a secret scan.
Existing PRDs stay intact and unstaged until publication clearance.
