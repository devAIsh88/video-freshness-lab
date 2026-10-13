# Repository instructions

- Read `PRD.md` and the full `Video_Freshness_Lab_PRD_v0.1.docx` before implementing.
  Read `docs/architecture/foundation.md` for differences and milestone limits.
  Preserve both originals; do not silently resolve contradictory requirements.
- Milestone 1.1 contains packaging, an import smoke test, documentation, and CI
  only. No producer, buffer, oracle, fault simulator, capture, or application API
  is implemented. Do not start Milestone 1.2 without authorization.
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
- Avoid unnecessary commits. Use milestone-based conventional Git history, with
  at most one Milestone 1.1 commit after all checks pass and owner approval of the
  staged diff. Proposed message: `chore: establish validation harness foundation`.
- Do not force-push or rewrite history. Do not create a remote, push, publish,
  deploy, choose a license, or change visibility without explicit owner approval.
- Record uncertainty and negative results. Stop at the authorized milestone and
  provide reviewable evidence instead of assuming productization is inevitable.
