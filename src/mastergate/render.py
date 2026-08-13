"""Portable evidence renderers for Mastergate batch checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import BatchCheck, WavMeasurement


READY_FILE_CHECK = "DECLARED FILE CHECKS PASSED"
INCOMPLETE_VERDICT = "RENDERED - QC INCOMPLETE"
BLOCKED_VERDICT = "BLOCKED - REQUIREMENTS OR MEDIA MISSING"


def render_report(batch: BatchCheck) -> str:
    """Render a readable result with explicit limits on what it proves."""

    contract = batch.contract
    lines = [
        f"# Mastergate report - {_markdown_cell(contract.delivery.title)}",
        "",
        "## Declared delivery contract",
        "",
        "| Field | Declared value |",
        "| --- | --- |",
        f"| Requirement basis | {_markdown_cell(contract.delivery.requirements_basis)} |",
        f"| Sample rate | {contract.audio_format.sample_rate_hz} Hz |",
        f"| Bit depth | {contract.audio_format.bit_depth} |",
        f"| Channels | {contract.audio_format.channels} |",
        f"| Expected WAV files | {len(contract.expected_files)} |",
        "",
        "## Measured PCM WAV files",
        "",
        "| File | Size | Frames | Duration | Sample peak | Boundary samples | SHA-256 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    lines.extend(_measurement_row(measurement) for measurement in batch.measurements)
    if not batch.measurements:
        lines.append("| No readable expected WAV files |  |  |  |  |  |  |")

    lines.extend(["", "## Declared file-check result", ""])
    if batch.is_passed:
        lines.extend(
            [
                READY_FILE_CHECK,
                "",
                "## Overall delivery verdict",
                "",
                INCOMPLETE_VERDICT,
                "",
                "The declared files passed this local file-level contract. This is not a true-peak, loudness, listening, source-integrity, upload, or recipient-acceptance verification.",
            ]
        )
    else:
        lines.extend([BLOCKED_VERDICT, "", "### Blocking findings", ""])
        lines.extend(f"- {_markdown_cell(error)}" for error in batch.errors)

    lines.extend(
        [
            "",
            "## Still unverified",
            "",
            "- Correct source/session, revisions, dependencies, and recall state.",
            "- Auditioning for clicks, dropouts, boundaries, tails, noise, and musical suitability.",
            "- Inter-sample true peak, integrated loudness, DC, phase, mono compatibility, and stem reconstruction.",
            "- Archive re-open, transfer, recipient receipt, platform processing, publication, and public access.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_manifest(batch: BatchCheck, contract_source: Path) -> str:
    """Render machine-readable measured facts without absolute input paths."""

    contract = batch.contract
    manifest = {
        "contract": {
            "assets": {"expected_files": list(contract.expected_files)},
            "delivery": {
                "requirements_basis": contract.delivery.requirements_basis,
                "title": contract.delivery.title,
            },
            "format": {
                "bit_depth": contract.audio_format.bit_depth,
                "channels": contract.audio_format.channels,
                "sample_rate_hz": contract.audio_format.sample_rate_hz,
            },
            "limits": {
                "max_sample_peak_dbfs": contract.limits.max_sample_peak_dbfs,
                "reject_full_scale_samples": contract.limits.reject_full_scale_samples,
            },
        },
        "contract_source": {
            "filename": contract_source.name,
            "sha256": _sha256(contract_source),
        },
        "declared_file_checks_passed": batch.is_passed,
        "errors": list(batch.errors),
        "input": {"directory_name": batch.input_directory.name},
        "measurements": [
            measurement_to_dict(measurement) for measurement in batch.measurements
        ],
        "overall_delivery_verdict": (
            INCOMPLETE_VERDICT if batch.is_passed else BLOCKED_VERDICT
        ),
        "schema_version": 1,
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_checksums(batch: BatchCheck) -> str:
    """Render standard two-space-separated checksums for measured files."""

    return "".join(
        f"{measurement.sha256}  {measurement.path.name}\n"
        for measurement in batch.measurements
    )


def batch_to_dict(batch: BatchCheck) -> dict[str, object]:
    """Return the check result for the CLI JSON mode."""

    return {
        "declared_file_checks_passed": batch.is_passed,
        "errors": list(batch.errors),
        "measurements": [measurement_to_dict(measurement) for measurement in batch.measurements],
        "overall_delivery_verdict": (
            INCOMPLETE_VERDICT if batch.is_passed else BLOCKED_VERDICT
        ),
    }


def measurement_to_dict(measurement: WavMeasurement) -> dict[str, object]:
    """Use a filename only, preserving portability and avoiding host paths."""

    return {
        "bit_depth": measurement.bit_depth,
        "byte_size": measurement.byte_size,
        "channels": measurement.channels,
        "duration_seconds": measurement.duration_seconds,
        "filename": measurement.path.name,
        "frame_count": measurement.frame_count,
        "full_scale_sample_count": measurement.full_scale_sample_count,
        "sample_peak_dbfs": measurement.sample_peak_dbfs,
        "sample_rate_hz": measurement.sample_rate_hz,
        "sha256": measurement.sha256,
    }


def _measurement_row(measurement: WavMeasurement) -> str:
    return "| {filename} | {size} | {frames} | {duration:.6f} s | {peak} | {boundaries} | `{sha256}` |".format(
        filename=_markdown_cell(measurement.path.name),
        size=measurement.byte_size,
        frames=measurement.frame_count,
        duration=measurement.duration_seconds,
        peak=_sample_peak_text(measurement.sample_peak_dbfs),
        boundaries=measurement.full_scale_sample_count,
        sha256=measurement.sha256,
    )


def _sample_peak_text(value: float | None) -> str:
    if value is None:
        return "digital silence"
    display = 0.0 if abs(value) < 0.005 else value
    return f"{display:.2f} dBFS (sample)"


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _sha256(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
