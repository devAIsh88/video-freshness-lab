# Public release readiness

Review updated 24 October 2026 for the original `devAIsh88/video-freshness-lab`,
default branch `main`, repository ID `1418013124`. Starting revision:
`355b8348280ffd97fc93785dacb4d5e113f94d5b`.

**Decision: MIT source publication authorized, subject to final private delivery
verification.** The owner explicitly confirmed ownership/necessary rights,
approved MIT with `Copyright (c) 2026 devAIsh88`, and accepted public exposure of
the existing Git author email and historical checkout path. These confirmations
resolve the previous ownership and disclosure blockers. They are owner statements,
not conclusions inferred from Git metadata.

The PIVOT outcome and unmet research/adoption gates remain unchanged. This is a
source recipe/toolkit publication, not a package release or production guarantee.
The original PRDs remain excluded. No second repository, history rewrite, GitHub
release, package publication, deployment or paid service is authorized.

## Source readiness at commit review

| Gate | Status | Evidence |
| --- | --- | --- |
| Exact repository/account/default branch | PASS | `devAIsh88` authenticated; original HTTPS origin; API confirms original ID, private visibility, main and owner administrator access |
| Starting Git synchronization/history | PASS | Local main and origin/main match the starting SHA; all 15 original commits recorded for post-publication comparison; foundation retained |
| Original-work rights confirmation | PASS | Owner explicitly confirmed ownership and necessary rights to release original contributions under MIT |
| License text and packaging | PASS | Unmodified GitHub standard MIT template with approved notice; `license = "MIT"`, `license-files = ["LICENSE"]`; editable/wheel metadata verified |
| Third-party redistribution | PASS | [Audit](THIRD_PARTY_LICENSE_REVIEW.md) identifies no blocker for this source-only distribution; no dependency source/binaries bundled; incomplete optional audit-dependency notices remain future-bundling limitations |
| Historical personal-data disclosure | PASS | Owner explicitly accepted existing email/path visibility; no raw values added to this report; history preserved |
| Current source and reachable history security | PASS | 15 commits/145 unique blobs reviewed; 13 scanner candidates are verified hashes/pins; no credentials, prohibited media or private camera endpoints identified |
| Available Actions history | PASS | All 17 run attempts and 87 log files reviewed; six entropy candidates are verified Git commit/blob identities; remaining paths are expected hosted-runner/Dependabot paths; zero retained artifacts |
| Original PRD exclusion | PASS | Both originals unchanged, untracked, absent from tracked/historical paths and review wheel; DOCX container inspected locally |
| Dependency advisory review | PASS | Exact eight core/build/tool and three image/tool package inventories rescanned; no known vulnerabilities reported; native-code analysis is outside this scan |
| CI configuration | PASS | Existing 3.11/3.12 matrix; SHA-pinned actions, read-only permissions, bounded jobs, pip check, no secrets/CD/publication |
| Local checks and CLI | PASS | Ruff lint/format, 305 pytest tests, pip check, diff checks, editable install, wheel metadata and existing simulator/reconnect CLI passed |
| Previous private delivery and CI baseline | PASS | Starting SHA pushed and synchronized; [CI run 39975199015](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39975199015) completed successfully on 3.11 and 3.12 |

The table records facts verifiable before this license commit. The exact new SHA,
its subsequent CI and actual public visibility cannot be known inside that same
commit. They are mandatory execution checks below, not preclaimed outcomes.
The final delivery report records those independently observed results.

## Mandatory execution checks after commit

1. Create exactly one `docs: finalize MIT license for public release` commit.
   Push it to the original private origin/main; confirm local, remote and API SHA
   equality and GitHub recognition of SPDX MIT with the exact LICENSE contents.
2. Require completed successful `checks (3.11)` and `checks (3.12)` jobs for that
   exact SHA, and review newly available Actions logs/artifacts. Preserve all
   previous commits and recheck source/security evidence for the new revision.
3. Reconfirm original repository ID/name, private visibility, approved rights,
   PRD exclusion, source-only redistribution and no unresolved security blocker.
   A failure or unavailable required result blocks the visibility command.
4. Only after all these gates pass, execute:

   ```sh
   gh repo edit devAIsh88/video-freshness-lab --visibility public --accept-visibility-change-consequences
   ```

5. Independently verify public API/anonymous access, MIT recognition, rendered
   README and documentation links, default branch and every original milestone
   SHA. Enable/verify supported free public security protections. No additional
   source commit is needed merely to claim its own visibility or CI result.

## Security and history method

Fetched all remote heads and tags without pruning or rewriting. Inspected branches,
tags, commits, reflogs, reachable tree/blob objects, contributor metadata, current
files, ignored-file categories, workflow, document containers and dependency
boundaries. The original PRD hashes match their foundation record. No original
PRD, environment, credential file, recording, archive or binary appears in the
reachable Git blobs. The review wheel contains only first-party Python and
package metadata. The initial no-license-grant notice has now been replaced
with the approved MIT text; the rebuilt wheel carries that exact notice.
The initial `git fsck` identified four local dangling blobs: all were UTF-8
drafts/configuration text, not either original PRD. Targeted inspection and an additional established scan
found no credential candidates. These unreachable blobs are not included in a
normal branch push; none was deleted or rewritten.

Used [Yelp detect-secrets](https://github.com/Yelp/detect-secrets) 1.5.0 in an
isolated temporary environment, with `--no-verify` so candidates were not sent
for live credential validation. Current scan: 13 potential matches, all artifact
hashes or pinned commits/source-integrity checks. Latest committed-history export:
146 files (145 blobs plus commit metadata), the same 13 explained candidates.
Actions: all 87 files selected, six candidates verified against actual Git commit/blob objects;
no credential candidates remain unexplained. Targeted checks supplemented entropy
scanning for credentials, private keys, private addresses, non-loopback RTSP endpoints,
embedded URL authentication, personal data and prohibited file types.

An initial absolute-path scanner invocation silently selected zero exported
files. It was invalid evidence and was replaced by runs **from inside each export
directory**, with `scan --no-verify --all-files .`; file coverage was checked.
Manual Actions review found hosted-runner paths, masked tokens and expected
credential setup/cleanup only. No credential rotation was identified as necessary.
Automated scans and manual screening cannot prove that undiscovered secrets or
ownership issues do not exist.

Historical contact/path metadata was a disclosure decision, not an exposed access
credential; the owner has now explicitly accepted that disclosure. Removing the
current demo path does not remove the older value from history. The existing
history has not been rewritten, and nothing has been removed from GitHub Actions
to conceal evidence.

## Dependencies and changes

The core still has no runtime dependencies. Exact reviewed dependency versions
were inventoried from the environments, with the isolated build requirement
added explicitly. [PyPA pip-audit](https://github.com/pypa/pip-audit) 2.9.0 queried
the advisory database using those exact pins (`--no-deps --disable-pip`). This
checks the enumerated installed/build packages; it is not a transitive lockfile
or a native-code vulnerability analysis.

| Finding | Change | Evidence |
| --- | --- | --- |
| pytest 8.4.2: CVE-2025-71176 / PYSEC-2026-1845 | Development pin and local tool changed to 9.0.3 | [Reviewed advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g); full suite remains 305 passing |
| setuptools 80.9.0: CVE-2026-59890 / PYSEC-2026-3447 | Isolated build pin changed to 83.0.0 | [PyPA advisory](https://github.com/pypa/advisory-database/blob/main/vulns/setuptools/PYSEC-2026-3447.yaml); editable and wheel builds passed |
| Optional image environment pip 26.0.1: four advisories | Upgraded only that environment to 26.2.1 | PYSEC-2026-196, -2875, -2876, -3721; image inventory rescanned clean |

Final advisory inventories: eight core/build/tool packages and three image/tool
packages, zero known vulnerabilities reported. Versions used in historical
experiment reports remain unchanged as historical evidence. Fedora native RPMs
and the disposable historical FrameGrab environment were license-reviewed, not
certified free of vulnerabilities by this Python advisory scan. Audit tooling
lives outside Git; no new runtime dependency was introduced.

## Verification performed

Fedora 44, project Python 3.12.15, pytest 9.0.3 and Ruff 0.14.0:

```sh
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip wheel --no-deps --wheel-dir /tmp/vfl-release-wheel .
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

Ruff: all checks passed, 40 Python files formatted. The prior preparation checkpoint
passed all 305 tests; the MIT delivery also passed all 305 in 1.67 seconds.
No test was removed or weakened. Packaging inventory and metadata were inspected.
The rebuilt 25-member wheel verifies Metadata 2.4, `License-Expression: MIT`,
`License-File: LICENSE` and the exact approved notice. Across the prior preparation
documentation, 144 relative links/heading anchors resolved inside
the publication tree; all 100 external source/documentation URLs returned successful
HTTP responses. The MIT update resolves 151 relative links/anchors. Repository
URLs and rendered public pages are rechecked after publication, together with
supported private vulnerability reporting.
The modern MIT declaration is [supported by the selected backend](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).

The preparation checkpoint executed the default simulation, all-suite JSON,
filtered reconnect, threaded normal/slow/idle, stamped-image single repetition
and six image integration methods. Also ran all existing native/RTSP/fault integration suites:

```sh
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_gstreamer_native.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_rtsp_transport.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_transport_faults.py -v
```

Native suite: 3 methods, 30 cases, 4.659 s. RTSP: 3 methods, 26 cases, 17.337 s.
Fault suite: 2 methods, 37 cases, 28.076 s. Tests positively check expected worker
termination, owned child exit, pipeline NULL and owned listening-port release.
A subsequent host process check found no remaining matching experiment workers.
GstRtspServer imports through `/usr/bin/python3`; RPM is
`gstreamer1-rtsp-server-1.28.8-1.fc44.x86_64`. This environment sees the Fedora host
installation. The MIT-only change reruns the ordinary suite, packaging and
simulator CLI; unchanged native-suite results are prior preparation evidence.
No large research cohort was repeated, and these regression counts are not added to historical reliability denominators or claimed as physical
camera freshness evidence.

## GitHub settings and visibility consequences

Verified description: “Reproducible Python experiments for video freshness, RTSP
buffering, recovery and session reliability.” Topics: python, rtsp, gstreamer,
computer-vision, video-streaming, pytest, fault-injection, reliability-engineering.
No homepage was invented.

Applied and read back:

- Actions limited to the existing checkout/setup-python full SHAs; SHA pinning
  required. Other GitHub-owned/verified actions are not implicitly allowed.
  Updating either action requires reviewing and updating this allowlist too.
  The CI install step explicitly selects reviewed pip 26.2.1 and now also runs
  `pip check`; ordinary CI still excludes native integration tests.
- Dependabot alerts and dependency graph enabled; SBOM endpoint works and open
  alerts were empty at review. An empty alert list is not a substitute for the
  explicit local advisory scan or a guarantee that graph ingestion is complete.
- Existing read-only workflow defaults and inability to approve PRs preserved.

Only the owner has collaborator access; no invitations, PRs, issues, webhooks,
deployments, environments, releases, tags or retained artifacts were found.
At the private checkpoint, branch protection/rulesets required a paid plan or
public visibility, and public secret scanning/private vulnerability reporting
were unavailable. No plan was upgraded. Supported free public protections are
checked after the authorized visibility transition.

[GitHub's visibility documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)
was evaluated: changing private to public exposes code/history and Actions logs,
permits public forks, publishes activity, can detach private forks, erases existing
stars/watchers, and disables push rulesets. There are currently no forks. Those
consequences were reviewed with the owner's explicit acceptance of historical
contact/path disclosure; current-tree cleanup alone would not remove that history.
The visibility command is gated on the exact new commit's private CI and license
verification. This source-review record does not preclaim its execution.

## Completion boundary

The former rights/disclosure blockers are resolved. Final publication succeeds
only when the mandatory execution checks above are actually observed. Any new
security/ownership issue requires keeping the repository private and reporting
the precise blocker. Research adoption, physical-camera evidence and package
productization remain separate unmet gates regardless of source visibility.
