"""TOML loading and validation for delivery contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib

from .models import AudioFormat, Delivery, DeliveryContract, Limits


class ContractFormatError(ValueError):
    """Raised when a contract cannot be structurally interpreted."""


@dataclass(frozen=True)
class ContractValidationReport:
    """All locally detectable contract problems in a stable order."""

    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


def load_contract(path: str | Path) -> DeliveryContract:
    """Load a declared delivery contract without changing it."""

    source = Path(path)
    try:
        data = tomllib.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ContractFormatError(f"contract file does not exist: {source}") from error
    except tomllib.TOMLDecodeError as error:
        raise ContractFormatError(f"could not parse TOML in {source}: {error}") from error

    delivery = _required_table(data, "delivery")
    audio_format = _required_table(data, "format")
    assets = _required_table(data, "assets")
    limits = data.get("limits", {})
    if not isinstance(limits, dict):
        raise ContractFormatError("[limits] must be a TOML table when supplied")

    return DeliveryContract(
        delivery=Delivery(
            title=_required_string(delivery, "title", "delivery"),
            requirements_basis=_required_string(
                delivery, "requirements_basis", "delivery"
            ),
        ),
        audio_format=AudioFormat(
            sample_rate_hz=_required_integer(audio_format, "sample_rate_hz", "format"),
            bit_depth=_required_integer(audio_format, "bit_depth", "format"),
            channels=_required_integer(audio_format, "channels", "format"),
        ),
        expected_files=_string_list(assets.get("expected_files"), "assets.expected_files"),
        limits=Limits(
            max_sample_peak_dbfs=_optional_number(
                limits.get("max_sample_peak_dbfs"), "limits.max_sample_peak_dbfs"
            ),
            reject_full_scale_samples=_optional_boolean(
                limits.get("reject_full_scale_samples"),
                "limits.reject_full_scale_samples",
                default=False,
            ),
        ),
    )


def validate_contract(contract: DeliveryContract) -> ContractValidationReport:
    """Return local contract problems without inventing a destination's rules."""

    errors: list[str] = []
    if not _is_nonblank_string(contract.delivery.title):
        errors.append("delivery.title must not be blank")
    if not _is_nonblank_string(contract.delivery.requirements_basis):
        errors.append("delivery.requirements_basis must not be blank")

    audio_format = contract.audio_format
    if not _is_positive_integer(audio_format.sample_rate_hz):
        errors.append("format.sample_rate_hz must be a positive integer")
    if audio_format.bit_depth not in {8, 16, 24, 32}:
        errors.append("format.bit_depth must be one of 8, 16, 24, 32")
    if not _is_positive_integer(audio_format.channels):
        errors.append("format.channels must be a positive integer")

    if not contract.expected_files:
        errors.append("assets.expected_files must contain at least one WAV filename")
    else:
        errors.extend(_validate_expected_files(contract.expected_files))

    limit = contract.limits.max_sample_peak_dbfs
    if limit is not None and (not _is_number(limit) or float(limit) > 0):
        errors.append("limits.max_sample_peak_dbfs must be less than or equal to 0 dBFS")
    if not isinstance(contract.limits.reject_full_scale_samples, bool):
        errors.append("limits.reject_full_scale_samples must be a boolean")

    return ContractValidationReport(tuple(errors))


def _required_table(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ContractFormatError(f"contract must contain a [{name}] table")
    return value


def _required_string(table: dict[str, Any], name: str, context: str) -> str:
    value = table.get(name)
    if not isinstance(value, str):
        raise ContractFormatError(f"{context}.{name} must be a string")
    return value


def _required_integer(table: dict[str, Any], name: str, context: str) -> int:
    value = table.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractFormatError(f"{context}.{name} must be an integer")
    return value


def _string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContractFormatError(f"{field_name} must be an array of strings")
    return tuple(value)


def _optional_number(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractFormatError(f"{field_name} must be a number")
    return float(value)


def _optional_boolean(value: Any, field_name: str, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ContractFormatError(f"{field_name} must be a boolean")
    return value


def _is_nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_expected_files(expected_files: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for filename in expected_files:
        normalized = filename.casefold() if isinstance(filename, str) else ""
        if normalized in seen:
            errors.append(
                "assets.expected_files contains duplicate names after case normalization: "
                f"'{normalized}'"
            )
        else:
            seen.add(normalized)

        if not _is_bare_wav_filename(filename):
            errors.append(
                "assets.expected_files entries must be bare .wav filenames: "
                f"'{filename}'"
            )
    return errors


def _is_bare_wav_filename(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("."):
        return False
    return Path(value).name == value and value.lower().endswith(".wav")
