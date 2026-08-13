"""Immutable models for a declared PCM WAV delivery contract."""

from __future__ import annotations

from dataclasses import dataclass


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
