# Repository instructions

- Read `PRD.md` and the full `Video_Freshness_Lab_PRD_v0.1.docx` before implementing.
  Read `docs/architecture/foundation.md` for differences and milestone limits.
  Preserve both originals; do not silently resolve contradictory requirements.
  The originals are intentionally absent from Git/GitHub. A fresh checkout must
  receive owner-provided local copies before requirement-dependent implementation;
  do not invent or download substitutes when they are missing.
- Research Stages 0–7 have been assessed; the outcome remains PIVOT to a
  reference recipe and reliability validation toolkit with unmet external gates.
  The owner now authorizes release preparation, security fixes, documentation,
  reviewed commits/private pushes, free GitHub security settings, and conditional
  public visibility. MIT with attribution `Copyright (c) 2026 devAIsh88` requires
  explicit confirmation of authority over the original material. Publication
  additionally requires every mandatory pre-publication gate in
  `docs/release/PUBLIC_RELEASE_READINESS.md` to pass. Do not infer legal authority from Git identity or routine continuation.
  Preserve drain-on-close. No new features, external posting, real cameras,
  package publication, GitHub releases, deployment or paid services are authorized.
- Use Python 3.11+, a `src/video_freshness_lab` layout, readable typed code, and
  standard-library components where possible. Do not add unnecessary dependencies.
  Document dependency purpose, version, license, and source before adoption.
- Keep the eventual source, application, evidence adapter, oracle, and report
  boundaries separate. Prefer identity, event ordering, sequence lag, and injected
  clocks over fragile real-time assertions. Do not claim an external defect or
  a standalone-package gap from demonstration code.
- Install editable with `python -m pip install -e ".[dev]"`. Run
  `python -m ruff check .`, `python -m ruff format --check .`, and
  `python -m pytest` for code changes. Report commands actually run, failures,
  missing tools, and platform limits. Do not substitute hand checks for pytest.
- Add meaningful behavioral tests when implementing contracts; synthetic data
  only, no hidden retries, no production network capture, and clean shutdown of
  any future threads. Keep integration evidence separate from pure tests.
- Never introduce secrets, private RTSP addresses, machine settings, real media,
  or credentials in files or output. Inspect ignored files and staged contents;
  scan document containers as well as text. Do not use `git add .` blindly.
- CI only: read-only permissions, no secrets, no deployment, no package/container
  publishing, no releases or paid services. Pin actions to full commit SHAs.
- Avoid unnecessary commits. Prefer one coherent, verified release-preparation
  commit: `chore: prepare video freshness lab for open-source release`. A blocked
  checkpoint must accurately state what remains unverified; it is not a release.
- Do not force-push, amend commits or rewrite history. Public visibility is
  authorized only after the mandatory legal, privacy, security and CI gates pass.
- Record uncertainty and negative results. Stop at the authorized milestone and
  provide reviewable evidence instead of assuming productization is inevitable.

## GitHub Repository and Milestone Delivery Policy

- Intended repository: `devAIsh88/video-freshness-lab`, initially PRIVATE, at
  `https://github.com/devAIsh88/video-freshness-lab`. Confirm the authenticated
  account is `devAIsh88`, ownership, private visibility, and existing branches
  before creation/reuse. Never overwrite unrelated remote history or initialize
  a separate remote README, license, or ignore file.
- Owner-authorized sequence: IMPLEMENT → TEST → SECURITY REVIEW → COMMIT → PUSH
  → VERIFY. Use one coherent conventional commit per successful milestone.
  Foundation commit `6ff7cb3f7aec0ee50175b22f85d0ad8642d052d0` must remain intact.
  Do not manufacture commits, amend milestones, or force-push.
- Before each commit run `.venv/bin/python -m ruff check .`,
  `.venv/bin/python -m ruff format --check .`, `.venv/bin/python -m pytest -v`,
  `.venv/bin/python -m pip check`, `git diff --check`, and
  `git diff --cached --check`. Verify editable packaging and review the full diff
  and staged filenames. Commit only after acceptance passes.
- Scan tracked/staged files and all history to be pushed for secrets, private
  connection data, media, datasets, environments, and temporary artifacts.
  `PRD.md` and `Video_Freshness_Lab_PRD_v0.1.docx` must remain unchanged and
  untracked, absent from every pushed commit. Sanitized `.env.example` is allowed.
- Push verified commits only to the intended private remote. Confirm the remote
  branch contains the exact SHA and review GitHub Actions status if accessible.
  Record commit SHA, push outcome, remote verification, and CI status. If several
  verified commits accumulated locally, push the existing history once; never
  manipulate history to fabricate individual deliveries.
- If authentication, repository creation, or network access is unavailable,
  preserve verified local work and record PUSH PENDING. Stop the affected remote
  action and report the blocker; continue safe local milestones. Do not request
  credentials unattended, perform authentication workarounds, or install tools
  requiring administrator access. Stop on a history security problem; do not
  rewrite history to hide it.
- CI only, never CD: Python/dependency setup, Ruff, pytest, and package validation
  with minimal permissions. No deployment, release, package/container publishing,
  paid runners, cloud provisioning, or paid infrastructure. Avoid unnecessary CI
  runs. Owner spending controls must prevent unexpected Actions overage charges;
  report any required owner configuration rather than enabling paid usage.
- Licensing remains blocked until the explicit ownership confirmation arrives.
  Keep private while any mandatory publication gate is FAIL, BLOCKED or NOT
  VERIFIED. After private push and passing CI, recheck identity and remote SHA
  before the authorized visibility change. Verify visibility independently.
  The original PRDs are excluded regardless of repository visibility.
