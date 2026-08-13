"""Read-only checking of a WAV directory against a declared contract."""

from __future__ import annotations

from pathlib import Path

from .contract import ContractValidationReport, validate_contract
from .models import BatchCheck, DeliveryContract, WavMeasurement
from .wav import WavInspectionError, inspect_wav


class InvalidContractError(ValueError):
    """Raised when a caller attempts to inspect media with an invalid contract."""

    def __init__(self, report: ContractValidationReport) -> None:
        self.report = report
        super().__init__("\n".join(report.errors))


class InputDirectoryError(ValueError):
    """Raised when the input directory cannot be safely inspected."""


def check_batch(contract: DeliveryContract, input_directory: str | Path) -> BatchCheck:
    """Inspect expected WAV files without changing the input directory."""

    report = validate_contract(contract)
    if not report.is_valid:
        raise InvalidContractError(report)

    directory = Path(input_directory)
    if not directory.is_dir():
        raise InputDirectoryError(f"input directory does not exist: {directory}")

    actual_paths = {
        path.name: path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.casefold() == ".wav"
    }
    expected_names = contract.expected_files
    expected_name_set = set(expected_names)
    errors: list[str] = []
    measurements: list[WavMeasurement] = []

    for name in expected_names:
        if name not in actual_paths:
            errors.append(f"missing expected WAV file: '{name}'")
    for name in sorted(set(actual_paths) - expected_name_set):
        errors.append(f"unexpected WAV file: '{name}'")

    for name in expected_names:
        path = actual_paths.get(name)
        if path is None:
            continue
        try:
            measurement = inspect_wav(path)
        except WavInspectionError as error:
            errors.append(f"{name}: {error}")
            continue

        measurements.append(measurement)
        errors.extend(_format_mismatches(name, measurement, contract))

    return BatchCheck(
        contract=contract,
        input_directory=directory,
        measurements=tuple(measurements),
        errors=tuple(errors),
    )


def _format_mismatches(
    name: str, measurement: WavMeasurement, contract: DeliveryContract
) -> list[str]:
    errors: list[str] = []
    expected = contract.audio_format
    if measurement.sample_rate_hz != expected.sample_rate_hz:
        errors.append(
            f"{name}: sample rate is {measurement.sample_rate_hz} Hz; "
            f"expected {expected.sample_rate_hz} Hz"
        )
    if measurement.bit_depth != expected.bit_depth:
        errors.append(
            f"{name}: bit depth is {measurement.bit_depth}; expected {expected.bit_depth}"
        )
    if measurement.channels != expected.channels:
        errors.append(f"{name}: channels is {measurement.channels}; expected {expected.channels}")

    max_sample_peak_dbfs = contract.limits.max_sample_peak_dbfs
    if (
        max_sample_peak_dbfs is not None
        and measurement.sample_peak_dbfs is not None
        and measurement.sample_peak_dbfs > max_sample_peak_dbfs
    ):
        errors.append(
            f"{name}: sample peak {_format_dbfs(measurement.sample_peak_dbfs)} dBFS exceeds "
            f"declared maximum {_format_dbfs(max_sample_peak_dbfs)} dBFS"
        )
    if (
        contract.limits.reject_full_scale_samples
        and measurement.full_scale_sample_count > 0
    ):
        errors.append(
            f"{name}: contains {measurement.full_scale_sample_count} full-scale boundary "
            "sample(s), which the contract rejects"
        )
    return errors


def _format_dbfs(value: float) -> str:
    """Avoid presenting a rounded full-scale boundary sample as '-0.00'."""

    return f"{0.0 if abs(value) < 0.005 else value:.2f}"
