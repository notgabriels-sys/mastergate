# Mastergate HTML Evidence Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a self-contained offline HTML evidence brief to each passing Mastergate WAV preflight build.

**Architecture:** Keep the existing pass-only atomic build boundary. Add one pure renderer in `src/mastergate/render.py` that derives a portable HTML document from `BatchCheck`, then have `build_evidence_files` write it inside the existing temporary output directory before its final atomic rename. The HTML is a review surface for measured facts, deliberately preserving Mastergate’s stated limit: it does not establish a full QC, approval, recipient acceptance, or release-compliance result.

**Tech Stack:** Python 3.11+, Python standard library (`html`, `pathlib`, `tempfile`), pytest, Hatchling.

## Global Constraints

- Produce exactly one additional evidence file named `MASTERGATE_EVIDENCE.html` for successful builds.
- Keep the package dependency-free at runtime; use only Python’s standard library for rendering and escaping.
- The HTML must be self-contained: no JavaScript, external assets, analytics, remote fonts, links, or network URLs.
- Escape every dynamic string with `html.escape(value, quote=True)` before interpolating it into markup.
- Show only `measurement.path.name`, never an input-directory, contract-source, or other host path in the HTML.
- Preserve existing pass-only build semantics, refusal to overwrite output, and atomic temporary-directory-to-final-directory replacement.
- Make no claim of rights, approval, recipient receipt, upload, platform processing, publication, public availability, true-peak, loudness, audition, source integrity, or full release compliance.
- Preserve `READY_FILE_CHECK`, `INCOMPLETE_VERDICT`, and `BLOCKED_VERDICT` semantics and wording where the existing rendered report exposes them.

## File Structure

- Modify: `src/mastergate/render.py` — pure `render_evidence_html(batch: BatchCheck) -> str` and small HTML-only formatting helpers.
- Modify: `src/mastergate/build.py` — add the HTML brief to the existing atomic success-only evidence package.
- Modify: `tests/test_render.py` — direct rendering, escaping, portability, and no-network/no-script regression tests.
- Modify: `tests/test_build.py` — assert the new file is written as part of a passing atomic build.
- Modify: `tests/test_cli.py` — assert the public `mastergate build` CLI exposes the new output file.
- Modify: `README.md` — document the HTML brief and its strict evidentiary boundary.

---

### Task 1: Specify the HTML renderer through failing tests

**Files:**
- Create: `tests/test_render.py`
- Modify: `tests/test_build.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `mastergate.check.check_batch(contract, input_directory)`, `tests.helpers.write_pcm_wav(path, sample_width_bytes, channels, frames)`.
- Produces: regression tests for `mastergate.render.render_evidence_html(batch: BatchCheck) -> str` and the fourth successful build output, `MASTERGATE_EVIDENCE.html`.

- [ ] **Step 1: Add a direct renderer test for measured facts, the QC boundary, and portable offline markup**

Create `tests/test_render.py` with a passing `BatchCheck` made from a 24-bit, stereo, 48 kHz fixture. Test the public renderer name that does not yet exist:

```python
html = render_evidence_html(batch)

assert html.startswith("<!doctype html>")
assert "DECLARED FILE CHECKS PASSED" in html
assert "RENDERED - QC INCOMPLETE" in html
assert "01-opening.wav" in html
assert "48,000 Hz" in html
assert str(input_directory) not in html
assert "http://" not in html
assert "https://" not in html
assert "<script" not in html
```

- [ ] **Step 2: Add an escaping regression test with markup-shaped delivery metadata and a filename**

Use a contract title of `Delivery <script>alert(1)</script> & "quoted"`, a requirements basis of `Basis <strong>not markup</strong> & more`, and a legal fixture filename of `01-<unsafe>&.wav`. Assert the output contains `&lt;script&gt;`, `&lt;strong&gt;`, `&quot;quoted&quot;`, and `01-&lt;unsafe&gt;&amp;.wav`, and does not contain raw `<script>alert(1)</script>` or raw `<strong>not markup</strong>`.

- [ ] **Step 3: Extend the passing build test before implementing the renderer**

In `tests/test_build.py`, make the expected `result.files` order explicit:

```python
assert [path.name for path in result.files] == [
    "MASTERGATE_REPORT.md",
    "MASTERGATE_EVIDENCE.html",
    "checksums.sha256",
    "manifest.json",
]
```

Read the generated HTML and assert its two existing status labels and the expected WAV filename are present. Keep the existing failed-build and overwrite-refusal assertions unchanged so the new file cannot weaken atomic or refusal behavior.

- [ ] **Step 4: Extend the CLI integration test before implementing the renderer**

In `tests/test_cli.py`, add this assertion to the successful `build` test:

```python
assert (output / "MASTERGATE_EVIDENCE.html").is_file()
```

- [ ] **Step 5: Run the focused tests to establish the expected failure**

Run: `python -m pytest tests/test_render.py tests/test_build.py tests/test_cli.py -q`

Expected: collection fails because `render_evidence_html` is not yet exported from `mastergate.render`; the build and CLI tests also fail until the fourth file is written.

- [ ] **Step 6: Commit the test specification**

```bash
git add tests/test_render.py tests/test_build.py tests/test_cli.py
git commit -m "test: specify Mastergate HTML evidence brief"
```

### Task 2: Implement a safe, self-contained HTML renderer

**Files:**
- Modify: `src/mastergate/render.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: `BatchCheck`, `WavMeasurement`, `READY_FILE_CHECK`, `INCOMPLETE_VERDICT`, `BLOCKED_VERDICT`.
- Produces: `render_evidence_html(batch: BatchCheck) -> str`, a complete UTF-8 HTML document with no external dependency.

- [ ] **Step 1: Add the standard-library escaping boundary**

Import Python’s `html` module in `src/mastergate/render.py`. Add a local helper that converts any dynamic value to text and escapes text and attributes safely:

```python
def _html(value: object) -> str:
    return html.escape(str(value), quote=True)
```

Use this helper for every dynamic string, including title, requirements basis, filename, errors, formatted checksum, and all dynamic data attributes if any are introduced.

- [ ] **Step 2: Implement the pure HTML renderer with the explicit evidence boundary**

Add the following public function near `render_report`:

```python
def render_evidence_html(batch: BatchCheck) -> str:
    """Render a portable offline evidence brief from a declared file check."""
```

Build the returned document with static inline CSS and no JavaScript. Include a `<meta charset="utf-8">`, one document title using the escaped delivery title, a header, a declared-contract table, a measured-files table, status text, and a `Still unverified` section. Render each measurement row using `measurement.path.name`, size, frame count, duration, sample peak, full-scale boundary count, and SHA-256. Format the sample rate with a thousands separator such as `48,000 Hz`.

For a passing batch, include `READY_FILE_CHECK`, `INCOMPLETE_VERDICT`, and this meaning in visible copy: the declared files passed a local file-level contract, but it is not a true-peak, loudness, listening, source-integrity, upload, or recipient-acceptance verification. For a non-passing batch rendered directly, use `BLOCKED_VERDICT` and an escaped list of the blocking errors.

Use static markup for the following visible limits so the brief cannot be mistaken for a release certificate:

```text
Correct source/session, revisions, dependencies, and recall state.
Auditioning for clicks, dropouts, boundaries, tails, noise, and musical suitability.
Inter-sample true peak, integrated loudness, DC, phase, mono compatibility, and stem reconstruction.
Archive re-open, transfer, recipient receipt, platform processing, publication, and public access.
```

End with a static statement that the document is generated locally from one declared file-level contract and does not establish rights, approval, recipient acceptance, upload, publication, or public availability.

- [ ] **Step 3: Keep styles static and complete enough for a handoff brief**

Use a small inline `<style>` block with readable system fonts, a neutral background, high-contrast text, a restrained status treatment, responsive table overflow, and print-friendly page margins. Do not include `@import`, `url(`, `script`, `iframe`, `img`, `a`, or form elements. Do not include paths other than escaped basenames inside the rendered tables.

- [ ] **Step 4: Run direct renderer tests and correct every escaping gap**

Run: `python -m pytest tests/test_render.py -q`

Expected: PASS. If the escaping fixture exposes raw markup, correct the renderer by applying `_html` at the interpolation boundary rather than weakening the test.

- [ ] **Step 5: Commit the renderer**

```bash
git add src/mastergate/render.py tests/test_render.py
git commit -m "feat: render offline Mastergate evidence brief"
```

### Task 3: Add the fourth output to the atomic build and document its scope

**Files:**
- Modify: `src/mastergate/build.py`
- Modify: `README.md`
- Test: `tests/test_build.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `render_evidence_html(batch: BatchCheck) -> str` from `mastergate.render` and the existing `BuildResult.files` tuple of `Path` values.
- Produces: a successful `mastergate build` directory containing four named portable evidence files, with `MASTERGATE_EVIDENCE.html` available through `BuildResult.files` and the CLI.

- [ ] **Step 1: Wire the pure renderer into the existing atomic temporary directory**

In `src/mastergate/build.py`, import `render_evidence_html`. Expand the immutable filename order:

```python
filenames = (
    "MASTERGATE_REPORT.md",
    "MASTERGATE_EVIDENCE.html",
    "checksums.sha256",
    "manifest.json",
)
```

After the Markdown report write and before the checksum and manifest writes, write the HTML output inside `temporary_path`:

```python
(temporary_path / "MASTERGATE_EVIDENCE.html").write_text(
    render_evidence_html(batch), encoding="utf-8"
)
```

Do not change the existing `if not batch.is_passed` guard, existing-output refusal, temporary-directory cleanup, or final `temporary_path.replace(output_path)` atomic publication.

- [ ] **Step 2: Update the README’s successful-output list and boundary**

Directly after `MASTERGATE_REPORT.md` in the output list, add:

```markdown
- `MASTERGATE_EVIDENCE.html` - a self-contained offline browser brief of the measured file facts and explicit QC boundary.
```

Add a concise paragraph immediately below the list stating that the brief is generated locally with no scripts, remote assets, or source media, and is a file-level review surface rather than a certificate, approval, recipient receipt, or release-compliance result.

- [ ] **Step 3: Run build and CLI regressions**

Run: `python -m pytest tests/test_build.py tests/test_cli.py -q`

Expected: PASS. Confirm the failed `build` still creates no output directory and the existing-output test still rejects replacement rather than merely checking that the HTML exists.

- [ ] **Step 4: Commit atomic packaging and documentation**

```bash
git add src/mastergate/build.py README.md tests/test_build.py tests/test_cli.py
git commit -m "feat: include HTML brief in Mastergate builds"
```

### Task 4: Verify distributable behavior and prepare the reviewed draft PR

**Files:**
- Verify: `src/mastergate/render.py`
- Verify: `src/mastergate/build.py`
- Verify: `tests/test_render.py`
- Verify: `tests/test_build.py`
- Verify: `tests/test_cli.py`
- Verify: `README.md`

**Interfaces:**
- Consumes: the four-file successful evidence pack and Python package metadata in `pyproject.toml`.
- Produces: a normal-pushed branch and a draft pull request with evidence-backed verification notes; no merge, deployment, package publication, analytics, or user-data processing.

- [ ] **Step 1: Run the complete local regression and static checks**

Run:

```bash
python -m pytest -q
python -m compileall -q src
git diff --check origin/main..HEAD
```

Expected: all tests pass, source compiles, and Git reports no whitespace errors.

- [ ] **Step 2: Validate an installed wheel in a fresh temporary environment**

Build a wheel with no dependency resolution, install it into a new temporary virtual environment, and use a synthetic 24-bit PCM WAV plus a minimal TOML contract to run the installed `mastergate build` command. Assert all four exact output names are present and inspect the HTML file text for `DECLARED FILE CHECKS PASSED`, `RENDERED - QC INCOMPLETE`, no `<script`, and no `http://` or `https://` strings.

- [ ] **Step 3: Perform a diff-scoped security review**

Review the diff from `origin/main` for dynamic HTML injection, host-path leakage, external requests, unsafe file writes, and scope creep. Confirm every dynamic HTML interpolation uses `html.escape(str(value), quote=True)`, only basenames are rendered, no remote URL or executable markup is generated, and the output stays within the pre-existing pass-only atomic build boundary. Record and resolve any concrete finding before pushing.

- [ ] **Step 4: Push a normal feature branch and create a draft pull request**

Run a normal push of `codex/mastergate-html-brief`. Create a draft PR against `main` titled `feat: add offline Mastergate evidence brief`. In the PR body, state the four evidence files, the offline/no-script boundary, local test result, wheel smoke result, and security-review result. Do not merge it, mark it ready, publish a package, create a release, enable telemetry, or make any client-facing claim.

- [ ] **Step 5: Verify the literal GitHub state**

Query the PR through GitHub and record: URL, `OPEN` state, `isDraft: true`, base branch `main`, exact head ref and SHA, clean mergeability if GitHub provides it, and workflow status. Report only observed state, distinguishing a draft PR from a merged feature or released product.

## Plan Self-Review

- Spec coverage: Task 1 defines the rendering, escaping, offline, and portability expectations through regressions. Task 2 adds the pure standard-library renderer and the exact QC boundary. Task 3 places the fourth output inside the existing atomic pass-only build and documents its limit. Task 4 verifies source, distribution behavior, security properties, and draft-PR state.
- No-placeholder review: every task lists exact files, public interfaces, command lines, expected outcomes, and concrete strings or code where an implementer must preserve a safety boundary.
- Type consistency: the only new public interface is `render_evidence_html(batch: BatchCheck) -> str`; Task 2 defines it, Task 3 consumes it, and Tasks 1 and 4 test it directly or through `build_evidence_files`.
