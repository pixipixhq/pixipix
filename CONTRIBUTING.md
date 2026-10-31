# Contributing to PixiPix

Thanks for helping improve PixiPix. Contributions of focused bug fixes,
tests, documentation, and well-scoped features are welcome.

PixiPix is a deterministic, local-first Python CLI. Changes should preserve
repeatable output, explicit configuration, safe filesystem behavior, and clear
failures instead of guessing.

## Before opening an issue

- Search existing issues and confirm the report is not already tracked.
- Use the bug form for incorrect or unexpected behavior.
- Use the feature form to describe a problem or workflow improvement before
  proposing a large implementation.
- Include the PixiPix version, Python version, operating system, installation
  method, minimal reproduction steps, and sanitized configuration where relevant.
- Reduce image examples to the smallest synthetic or redistributable fixture that
  still demonstrates the behavior.

Do not post credentials, private artwork, proprietary source images, personal
information, or security-vulnerability details in a public issue. Report security
problems through [GitHub private vulnerability reporting][private-report]. If that
form is unavailable, contact the maintainer through GitHub before sharing details.

[private-report]: https://github.com/pixipixhq/pixipix/security/advisories/new

## Development setup

PixiPix requires Python 3.12 and uses `uv` for its locked environment.

```bash
git clone https://github.com/YOUR-USERNAME/pixipix.git
cd pixipix
uv sync --locked --all-groups
uv run python --version
uv run pixipix --help
```

Use a focused branch in your fork. Keep unrelated refactors and generated files
out of the change.

## Making changes

- Add or update tests for behavior changes and regressions.
- Keep CLI code limited to parsing, invocation, rendering, and error mapping.
- Keep deterministic serialization centralized and avoid timestamps, absolute
  machine paths, or other environment-specific values in public artifacts.
- Preserve explicit source-pixel and logical-pixel coordinate semantics.
- Do not weaken input limits, path validation, output ownership checks, or atomic
  publication behavior without a documented security review.
- Prefer tiny programmatically generated test fixtures.
- Do not modify or expose `docs-internal/` content.
- Do not commit `dist/`, caches, virtual environments, or temporary extraction
  output.

### Asset distribution policy

- **Test fixtures** must be neutral and redistributable. Document their provenance,
  permitted use, and distribution status; package them only when automated package or
  distribution tests require them.
- **Public examples** may use branded or rights-reserved material and do not need neutral
  terminology. Rights-reserved example assets stay repository-only unless their asset
  license explicitly permits package redistribution.
- **Brand assets**, including Pixi, the PixiPix logo, and derivatives containing them,
  are reserved repository content and must not enter wheels or source distributions.

See [ASSET-LICENSES.md](ASSET-LICENSES.md) before adding or changing branded visuals.
Every committed visual fixture or example asset must document its source or creator,
permitted use, and whether it may be included in package distributions.

## Verification

Run the portable contributor checks before requesting review:

```bash
uv sync --locked --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest -m "not canonical"
uv build
```

This selection includes unit, integration, architecture, packaging, and portable
parity-guard tests. It excludes only the six exact-environment qualification cases
marked `canonical`, matching the portable CI selection. Use a full-history clone:
the historical authority tests read immutable commits with `git show`.

Use `uv run ruff format .` to apply formatting. For a shorter feedback loop while
developing:

```bash
uv run pytest tests/unit tests/integration
```

Targeted tests do not replace the portable checks before review. Platform-specific
cases report explicit skips where their filesystem behavior is unavailable.

Exact-byte qualification is a separate gate. The current reference environment is
CPython 3.12.12 on macOS arm64, with the dependency versions in `uv.lock`. In that
environment, run the development suite, including canonical checks:

```bash
uv sync --locked --all-groups --python 3.12.12
uv run --no-sync pytest -m "not release_certificate"
```

To run only development parity there, use
`uv run --no-sync pytest -m "canonical and not release_certificate"`.
The two `release_certificate` cases separately certify installed artifacts against
an immutable release authority and its exact source lock. Run them with
`uv run --no-sync pytest -m release_certificate` when certifying that release.
A development lock change does not update or satisfy a historical certificate.
Plain `pytest` still selects every test, including strict release certificates;
the hard canonical-runtime precheck intentionally fails outside the reference
environment. Portable success does not establish byte parity or release eligibility.
See [the parity contract](tests/parity/README.md) for the historical authorities and
non-skipping release gates.

When package or release infrastructure changes, add focused release-script or
workflow-contract tests and coordinate the verification plan with the maintainer.
Contributors must not publish packages, create release tags, or change the package
version unless the maintainer has explicitly scoped that work.

## Pull requests

A reviewable pull request should:

- explain the problem and the chosen solution;
- describe user-visible, compatibility, security, or determinism effects;
- link related issues;
- include focused tests and documentation updates;
- list the exact verification commands run and their results;
- call out limitations and intentionally deferred work; and
- contain no secrets, generated distributions, or unrelated changes.

Keep commits understandable and use clear imperative commit messages. Maintainers
may ask for a change to be split when independent concerns are combined.

## Licensing

By submitting a contribution, you agree that it may be distributed under the
repository's [Apache License 2.0](LICENSE). Only submit work that you have the right
to contribute.
