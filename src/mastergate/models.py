"""Immutable models for a declared PCM WAV delivery contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Delivery:
    """Declared delivery identity and the evidence basis for its requirements."""

    title: str
    requirements_basis: str


@dataclass(frozen=True)
class AudioFormat:
    """Declared integer PCM WAV header requirements."""

    sample_rate_hz: int
    bit_depth: int
    channels: int


@dataclass(frozen=True)
class Limits:
    """Optional declared sample-level limits, never universal defaults."""

    max_sample_peak_dbfs: float | None = None
    reject_full_scale_samples: bool = False


@dataclass(frozen=True)
class DeliveryContract:
    """The complete local contract used to inspect one expected WAV batch."""

    delivery: Delivery
    audio_format: AudioFormat
    expected_files: tuple[str, ...]
    limits: Limits


@dataclass(frozen=True)
class WavMeasurement:
    """Facts measured from one readable integer PCM WAV file."""

    path: Path
    byte_size: int
    sha256: str
    sample_rate_hz: int
    bit_depth: int
    channels: int
    frame_count: int
    duration_seconds: float
    sample_peak_dbfs: float | None
    full_scale_sample_count: int


@dataclass(frozen=True)
class BatchCheck:
    """Declared file-check result, not a complete delivery approval."""

    contract: DeliveryContract
    input_directory: Path
    measurements: tuple[WavMeasurement, ...]
    errors: tuple[str, ...] = ()

    @property
    def is_passed(self) -> bool:
        return not self.errors
