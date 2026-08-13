from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mastergate.build import (
    DeclaredFileCheckFailedError,
    OutputDirectoryExistsError,
    build_evidence_files,
)
from mastergate.check import check_batch
from mastergate.contract import load_contract

from .helpers import write_pcm_wav


def test_build_evidence_files_writes_portable_report_manifest_and_checksums(
    write_contract, tmp_path: Path
) -> None:
    contract_path = write_contract(_contract_toml())
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(
        input_directory / "01-opening.wav",
        sample_width_bytes=3,
        channels=2,
        frames=((0, 0), (4194304, -4194304)),
    )
    batch = check_batch(load_contract(contract_path), input_directory)
    output = tmp_path / "evidence"

    result = build_evidence_files(batch, contract_path, output)

    assert result.output == output
    assert [path.name for path in result.files] == [
        "MASTERGATE_REPORT.md",
        "checksums.sha256",
        "manifest.json",
    ]
    report = (output / "MASTERGATE_REPORT.md").read_text(encoding="utf-8")
    assert "# Mastergate report - Example WAV delivery" in report
    assert "Requirement basis | Provisional local contract - confirm with recipient." in report
    assert "DECLARED FILE CHECKS PASSED" in report
    assert "RENDERED - QC INCOMPLETE" in report
    assert "not a true-peak, loudness, listening, source-integrity, upload, or recipient-acceptance verification" in report

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["contract_source"] == {
        "filename": "delivery.toml",
        "sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
    }
    assert manifest["declared_file_checks_passed"] is True
    assert manifest["overall_delivery_verdict"] == "RENDERED - QC INCOMPLETE"
    assert manifest["measurements"][0]["filename"] == "01-opening.wav"
    assert manifest["measurements"][0]["sample_peak_dbfs"] == pytest.approx(-6.0206)
    assert str(input_directory) not in (output / "manifest.json").read_text(encoding="utf-8")

    checksum_line = (output / "checksums.sha256").read_text(encoding="utf-8")
    assert checksum_line.endswith("  01-opening.wav\n")
    assert len(checksum_line.split("  ")[0]) == 64


def test_build_evidence_files_refuses_failed_declared_file_checks(
    write_contract, tmp_path: Path
) -> None:
    contract_path = write_contract(_contract_toml())
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    batch = check_batch(load_contract(contract_path), input_directory)
    output = tmp_path / "evidence"

    with pytest.raises(DeclaredFileCheckFailedError, match="missing expected WAV file"):
        build_evidence_files(batch, contract_path, output)

    assert not output.exists()


def test_build_evidence_files_refuses_to_replace_existing_output(
    write_contract, tmp_path: Path
) -> None:
    contract_path = write_contract(_contract_toml())
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(input_directory / "01-opening.wav", sample_width_bytes=3, channels=2)
    batch = check_batch(load_contract(contract_path), input_directory)
    output = tmp_path / "evidence"
    output.mkdir()

    with pytest.raises(OutputDirectoryExistsError, match="refusing to replace existing output"):
        build_evidence_files(batch, contract_path, output)


def _contract_toml() -> str:
    return """
[delivery]
title = "Example WAV delivery"
requirements_basis = "Provisional local contract - confirm with recipient."

[format]
sample_rate_hz = 48000
bit_depth = 24
channels = 2

[assets]
expected_files = ["01-opening.wav"]

[limits]
max_sample_peak_dbfs = -1.0
reject_full_scale_samples = true
""".strip()
