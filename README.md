# Mastergate

Mastergate is an offline preflight for a declared batch of integer PCM WAV
files. It checks actual files against one explicit delivery contract, then can
write a portable local evidence pack with measurements and SHA-256 checksums.

It exists to make basic delivery facts visible before handoff. It does not
replace an engineer's audition, source/session inspection, recipient brief, or
approval process.

## What it proves

For every expected WAV file, Mastergate can read and record:

- Presence, nonzero size, SHA-256 checksum, and PCM WAV readability.
- Sample rate, integer bit depth, channel count, frame count, and duration.
- Exact integer sample peak and count of full-scale boundary samples.
- Whether those measured facts match the requirements you explicitly declared.

`mastergate check` is read-only. `mastergate build` creates a new evidence
directory only when every declared file-level check passes; it never changes
your source audio and never replaces an existing output directory.

## What it does **not** prove

A passing result is deliberately reported as `RENDERED - QC INCOMPLETE`. It
does not prove the correct source/session, musical or technical audition,
click/dropout/tail inspection, true peak, integrated loudness, DC, phase,
mono compatibility, stem reconstruction, archive integrity, transfer,
recipient receipt, platform processing, publication, or public availability.

Mastergate does **not** impose a universal LUFS or true-peak target. If you add
`max_sample_peak_dbfs`, it is a declared **sample**-peak limit only, not an
inter-sample true-peak measurement. Record where requirements came from in
`delivery.requirements_basis`; if they are assumptions, label them provisional.

## Install from a checkout

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

Or install the command for regular use:

```sh
uv tool install --editable .
```

## Use

Start with [examples/delivery-example.toml](examples/delivery-example.toml),
then replace the generic names and requirements with the actual written brief.

```sh
mastergate check examples/delivery-example.toml ./masters
mastergate check examples/delivery-example.toml ./masters --json
mastergate build examples/delivery-example.toml ./masters --output ./delivery/mastergate-evidence
```

When a declared check passes, the build writes:

- `MASTERGATE_REPORT.md` - a readable measured-file report and QC boundary.
- `MASTERGATE_EVIDENCE.html` - a self-contained offline browser brief of the
  measured file facts and explicit QC boundary.
- `manifest.json` - contract, measurements, findings, and file-level state.
- `checksums.sha256` - checksums for the measured WAV files.

The HTML brief is generated locally with no scripts, remote assets, or source
media. It is a file-level review surface, not a certificate, approval,
recipient receipt, or release-compliance result.

When the batch fails, `check` exits with status `1`; `build` leaves no output
directory. Invalid contracts and unsafe attempts to overwrite output exit with
status `2`.

## Contract format

```toml
[delivery]
title = "Example WAV delivery"
requirements_basis = "Provisional local contract - confirm with recipient."

[format]
sample_rate_hz = 48000
bit_depth = 24
channels = 2

[assets]
expected_files = ["01-opening.wav", "02-closing.wav"]

[limits]
max_sample_peak_dbfs = -1.0       # optional; sample peak, not true peak
reject_full_scale_samples = true  # optional; defaults to false
```

The first version supports only uncompressed integer PCM WAV files with 8-,
16-, 24-, or 32-bit samples. AIFF, FLAC, MP3, float WAV, and other formats are
outside scope rather than silently misread.

## Development

```sh
.venv/bin/python -m pytest -q
```

The runtime depends only on Python 3.11+ and the standard library.
