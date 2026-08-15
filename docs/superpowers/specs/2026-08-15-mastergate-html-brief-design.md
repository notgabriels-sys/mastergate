# Mastergate offline HTML evidence brief — design

**Date:** 2026-08-15

## Purpose

Make a passing Mastergate evidence pack readable in any browser without asking a
reviewer to render Markdown or inspect JSON. The result should preserve the
tool's local-only, measured-file boundary and make the deliberately incomplete
QC verdict impossible to miss.

## Context

Mastergate already measures a declared batch of integer PCM WAV files and, only
when the declared file checks pass, writes three portable outputs:

- `MASTERGATE_REPORT.md`
- `manifest.json`
- `checksums.sha256`

The information is complete for technical review, but the browser-readable
format is missing. Releaseforge, Mixintake, and Scopequote already demonstrate
the practical value of self-contained review surfaces. The gap is particularly
relevant when an artist, engineer, manager, or label collaborator needs to read
the local facts and the remaining QC boundary without opening tooling files.

## Decision

Add `MASTERGATE_EVIDENCE.html` to every successful Mastergate build. It is a
fully self-contained, offline HTML document derived from the same `BatchCheck`
that already produces the Markdown report, manifest, and checksum file.

The output is a review brief, not a mastering report, certificate, approval,
delivery receipt, or platform-compliance document. It keeps the existing
`DECLARED FILE CHECKS PASSED` and `RENDERED - QC INCOMPLETE` language and the
existing list of still-unverified matters.

## Output shape

The document contains, in this order:

1. A clear title and local-only subtitle.
2. A prominent verdict block that says `DECLARED FILE CHECKS PASSED` and
   `RENDERED - QC INCOMPLETE`.
3. A declared contract table: title, requirement basis, sample rate, bit depth,
   channels, expected file count, optional sample-peak limit, and full-scale
   sample rule.
4. A measured-file table: filename, bytes, duration, format, sample peak,
   full-scale sample count, and SHA-256.
5. A concise `Still unverified` list copied semantically from the current
   Markdown boundary.
6. A final statement that the document was generated locally from one declared
   file-level contract and does not establish rights, approval, recipient
   acceptance, upload, publication, or public availability.

The document uses inline CSS only. It makes no network request, uses no
JavaScript, external font, image, analytics, tracker, or remote asset, and does
not link to source files.

## Rendering and data boundaries

Add one renderer in `src/mastergate/render.py` named
`render_evidence_html(batch: BatchCheck) -> str`.

All dynamic strings—including declared delivery title, requirement basis,
filenames, errors, and checksum values—must be passed through `html.escape`
before interpolation into HTML. Numeric facts may be formatted as text after
they are measured. The renderer must use only `measurement.path.name`; it must
not render an absolute input directory, the full measurement path, or the
contract file path.

The HTML renderer shares data with the existing `BatchCheck` and does not read
the WAV files, re-run checks, parse user paths, or change the contract schema.

## Build behavior

Update `build_evidence_files` so that a successful atomic build writes four
files in the temporary directory before the final rename:

```text
MASTERGATE_REPORT.md
MASTERGATE_EVIDENCE.html
checksums.sha256
manifest.json
```

The build remains forbidden for failed file checks and for an existing output
directory. A partial write remains cleaned up by the existing exception path.

## Documentation and validation

Update the README output list and scope copy to name the offline HTML evidence
brief precisely. Do not broaden Mastergate's supported formats or claim it
measures loudness, true peak, listening quality, rights, platform processing,
recipient acceptance, transfer, publication, or public availability.

Add focused tests that prove:

1. A passing build contains the fourth file and expected local/unfinished-QC
   verdicts.
2. Dynamic title, basis, and filename content is HTML escaped.
3. The HTML contains no input-directory path and no network, script, or external
   asset reference.
4. Existing no-overwrite and failed-build behavior is unchanged.

Run the full test suite, bytecode compilation, a clean build, and a fresh
wheel-install smoke run that creates all four evidence files from synthetic
temporary WAV data.

## Acceptance criteria

- A passing `mastergate build` produces the four listed files atomically.
- `MASTERGATE_EVIDENCE.html` opens offline, contains the measured file-level
  facts and explicit incomplete-QC boundary, and leaks no absolute input path.
- Every dynamic value is HTML escaped and the document references no remote
  resource or executable script.
- No supported format, technical measurement, approval, or delivery claim is
  broadened beyond the existing Mastergate boundary.
- The change is shipped as a normal draft PR from
  `codex/mastergate-html-brief`; it does not merge, publish a package, send a
  client artifact, or process real user audio.
