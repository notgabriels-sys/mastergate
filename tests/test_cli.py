from __future__ import annotations

import json
from pathlib import Path

from mastergate.cli import main

from .helpers import write_pcm_wav


def test_check_reports_declared_file_pass_and_incomplete_overall_qc(
    write_contract, tmp_path: Path, capsys
) -> None:
    contract_path = write_contract(_contract_toml())
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(input_directory / "01-opening.wav", sample_width_bytes=3, channels=2)

    assert main(["check", str(contract_path), str(input_directory)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == (
        "DECLARED FILE CHECKS PASSED (1 WAV file).\n"
        "Overall delivery verdict: RENDERED - QC INCOMPLETE.\n"
    )


def test_check_can_emit_machine_readable_evidence_boundary(
    write_contract, tmp_path: Path, capsys
) -> None:
    contract_path = write_contract(_contract_toml())
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(input_directory / "01-opening.wav", sample_width_bytes=3, channels=2)

    assert main(["check", str(contract_path), str(input_directory), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["declared_file_checks_passed"] is True
    assert payload["overall_delivery_verdict"] == "RENDERED - QC INCOMPLETE"
    assert payload["errors"] == []
    assert payload["measurements"][0]["filename"] == "01-opening.wav"


def test_build_creates_evidence_only_after_a_passing_file_check(
    write_contract, tmp_path: Path, capsys
) -> None:
    contract_path = write_contract(_contract_toml())
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(input_directory / "01-opening.wav", sample_width_bytes=3, channels=2)
    output = tmp_path / "evidence"

    assert main(["build", str(contract_path), str(input_directory), "--output", str(output)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == f"Built Mastergate evidence files: {output}\n"
    assert (output / "MASTERGATE_REPORT.md").is_file()
    assert (output / "manifest.json").is_file()
    assert (output / "checksums.sha256").is_file()


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
