"""Read-only integer PCM WAV header and sample-level inspection."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
import wave

from .models import WavMeasurement


class WavInspectionError(ValueError):
    """Raised when a file cannot be measured as an integer PCM WAV file."""


def inspect_wav(path: str | Path) -> WavMeasurement:
    """Measure actual WAV file facts and exact integer sample peak.

    The measurement is explicitly sample peak, not inter-sample true peak, and
    this function performs no auditioning or subjective audio-quality verdict.
    """

    source = Path(path)
    if not source.is_file():
        raise WavInspectionError("file does not exist")
    byte_size = source.stat().st_size
    if byte_size == 0:
        raise WavInspectionError("file is empty")

    try:
        with wave.open(str(source), "rb") as reader:
            if reader.getcomptype() != "NONE":
                raise WavInspectionError("file is not uncompressed PCM WAV")
            channels = reader.getnchannels()
            sample_width_bytes = reader.getsampwidth()
            sample_rate_hz = reader.getframerate()
            declared_frame_count = reader.getnframes()
            if channels < 1:
                raise WavInspectionError("header declares no channels")
            if sample_rate_hz < 1:
                raise WavInspectionError("header declares an invalid sample rate")
            if sample_width_bytes not in {1, 2, 3, 4}:
                raise WavInspectionError(
                    "unsupported integer PCM sample width "
                    f"({sample_width_bytes * 8} bits)"
                )
            peak, full_scale_count, actual_frame_count = _scan_samples(
                reader, channels, sample_width_bytes
            )
    except WavInspectionError:
        raise
    except (EOFError, wave.Error) as error:
        raise WavInspectionError(f"could not read PCM WAV data: {error}") from error

    if actual_frame_count != declared_frame_count:
        raise WavInspectionError(
            "WAV data frame count does not match header "
            f"({actual_frame_count} found, {declared_frame_count} declared)"
        )

    bit_depth = sample_width_bytes * 8
    sample_peak_dbfs = _peak_dbfs(peak, bit_depth)
    return WavMeasurement(
        path=source,
        byte_size=byte_size,
        sha256=_sha256(source),
        sample_rate_hz=sample_rate_hz,
        bit_depth=bit_depth,
        channels=channels,
        frame_count=declared_frame_count,
        duration_seconds=declared_frame_count / sample_rate_hz,
        sample_peak_dbfs=sample_peak_dbfs,
        full_scale_sample_count=full_scale_count,
    )


def _scan_samples(reader: wave.Wave_read, channels: int, sample_width_bytes: int) -> tuple[int, int, int]:
    frame_width = channels * sample_width_bytes
    maximum_absolute_sample = 0
    full_scale_sample_count = 0
    actual_frame_count = 0
    full_scale = 2 ** (sample_width_bytes * 8 - 1)
    full_scale_boundary = full_scale - 1

    while data := reader.readframes(65536):
        if len(data) % frame_width:
            raise WavInspectionError("audio data ends partway through a frame")
        actual_frame_count += len(data) // frame_width
        for sample in _iter_signed_samples(data, sample_width_bytes):
            absolute_sample = abs(sample)
            maximum_absolute_sample = max(maximum_absolute_sample, absolute_sample)
            if absolute_sample >= full_scale_boundary:
                full_scale_sample_count += 1

    return maximum_absolute_sample, full_scale_sample_count, actual_frame_count


def _iter_signed_samples(data: bytes, sample_width_bytes: int):
    if sample_width_bytes == 1:
        yield from (value - 128 for value in data)
        return
    for offset in range(0, len(data), sample_width_bytes):
        yield int.from_bytes(
            data[offset : offset + sample_width_bytes], byteorder="little", signed=True
        )


def _peak_dbfs(peak: int, bit_depth: int) -> float | None:
    if peak == 0:
        return None
    full_scale = 2 ** (bit_depth - 1)
    return 20 * math.log10(peak / full_scale)


def _sha256(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
