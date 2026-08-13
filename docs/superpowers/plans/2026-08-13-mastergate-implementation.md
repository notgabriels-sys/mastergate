# Mastergate implementation plan

> **Implementation note:** Complete every task test-first on an isolated
> feature branch. Use generated synthetic PCM WAV fixtures only; do not claim
> verification against real release audio without user-provided files.

## Task 1: Contract parser and validation

**Files:**

- Create: `pyproject.toml`
- Create: `src/mastergate/models.py`
- Create: `src/mastergate/contract.py`
- Create: `tests/test_contract.py`

1. Write failing tests for valid contracts and structural/semantic failures.
2. Run them to observe the missing-package failure.
3. Implement immutable contract models and TOML parsing.
4. Re-run focused and complete tests, then commit.

## Task 2: WAV inspection and declared-file checking

**Files:**

- Create: `src/mastergate/wav.py`
- Create: `src/mastergate/check.py`
- Create: `tests/helpers.py`
- Create: `tests/test_wav.py`
- Create: `tests/test_check.py`

1. Write fixtures and failing tests for WAV headers, exact sample peak, batch
   mismatches, and declared threshold failures.
2. Implement standard-library PCM WAV inspection and read-only batch checks.
3. Make evidence boundaries explicit in domain results.
4. Re-run focused and complete tests, then commit.

## Task 3: Build reports and command-line interface

**Files:**

- Create: `src/mastergate/render.py`
- Create: `src/mastergate/build.py`
- Create: `src/mastergate/cli.py`
- Create: `tests/test_build.py`
- Create: `tests/test_cli.py`

1. Write failing tests for report/manifest/checksum outputs, safe output
   creation, and command statuses.
2. Implement atomic builds and `check`/`build` commands.
3. Add example contract, README, and license.
4. Run the complete suite, installed-command smoke test, and wheel/sdist build.
5. Commit the finished behavior.

## Task 4: Publish and independently verify

1. Inspect the final diff and branch state.
2. Create the GitHub repository, push `main` and the feature branch, and open
   a PR.
3. Verify it is mergeable, merge it, and test a fresh clone from remote.
4. Continue to another focused tool after the repository is genuinely done.
