# Mastergate design

## Purpose

Mastergate is an offline preflight for a batch of PCM WAV files. It checks the
actual exported files against a declared contract before they are handed to a
label, client, mastering engineer, archive, or other recipient.

It is intentionally narrower than full audio QC. Its job is to make basic
format, file-list, and sample-peak facts visible and repeatable without
inventing a recipient's technical requirements.

## Commands

```text
mastergate check CONTRACT_TOML INPUT_DIRECTORY [--json]
mastergate build CONTRACT_TOML INPUT_DIRECTORY --output OUTPUT_DIRECTORY
```

`check` is read-only. It inspects expected WAV files in the given directory
without changing input files.

`build` runs the same checks first. Only a batch that passes every declared
file-level requirement can produce a new output directory with:

- `MASTERGATE_REPORT.md` - readable measured-file report and evidence boundary.
- `manifest.json` - all declared requirements and measured file facts.
- `checksums.sha256` - SHA-256 hashes of files that passed the declared checks.

Existing output directories are never replaced.

## Declared delivery contract

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
max_sample_peak_dbfs = -1.0 # optional
reject_full_scale_samples = true # optional
```

The contract is an explicit declaration, not evidence that a client,
distributor, or platform has accepted it. `requirements_basis` is required so
the report preserves whether a requirement came from a brief or is provisional.

## Actual checks

For each expected file, Mastergate records:

- presence, nonzero size, SHA-256 hash, PCM WAV readability;
- sample rate, bit depth, channel count, frame count, and duration;
- exact integer sample peak in dBFS and the count of full-scale boundary
  samples, for 8-, 16-, 24-, and 32-bit integer PCM WAV files.

It fails the declared check for missing or unexpected WAV assets, duplicate
expected names, incompatible headers, unreadable/audio formats, declared
sample-peak limit breaches, or a rejected full-scale sample count.

## Evidence boundary and verdict

A passing file check means `DECLARED FILE CHECKS PASSED`; it is not a delivery
approval. The generated report still labels the overall state
`RENDERED - QC INCOMPLETE` because Mastergate cannot verify source integrity,
auditioning, clicks/dropouts, true peak, integrated loudness, phase/mono,
inter-stem reconstruction, archive re-open, upload, receipt, or public access.

When a declared check fails, the report/CLI state is
`BLOCKED - REQUIREMENTS OR MEDIA MISSING`.

Mastergate never applies a universal LUFS or true-peak target. A sample-peak
limit exists only when the contract declares one, and it is reported as a
sample measurement rather than an inter-sample true-peak reading.

## Deliberate exclusions

- WAV only in the first version; AIFF, FLAC, MP3, and codecs are rejected or
  outside scope rather than silently misread.
- No audio alteration, conversion, normalisation, rendering, upload, zipping,
  or recipient communication.
- No listening verdict or substitute for a mastering engineer/client brief.
