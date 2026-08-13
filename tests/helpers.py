from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import wave


def write_pcm_wav(
    path: Path,
    *,
    sample_rate_hz: int = 48000,
    sample_width_bytes: int = 3,
    channels: int = 2,
    frames: Iterable[tuple[int, ...]] = ((0, 0),),
) -> Path:
    """Write a small integer PCM WAV fixture with explicit sample values."""

    encoded_frames = []
    for frame in frames:
        if len(frame) != channels:
            raise ValueError("fixture frame channel count does not match channels")
        encoded_frames.append(
            b"".join(_encode_sample(sample, sample_width_bytes) for sample in frame)
        )

    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(sample_width_bytes)
        writer.setframerate(sample_rate_hz)
        writer.writeframes(b"".join(encoded_frames))
    return path


def _encode_sample(value: int, sample_width_bytes: int) -> bytes:
    if sample_width_bytes == 1:
        if not -128 <= value <= 127:
            raise ValueError("8-bit fixture sample is out of range")
        return bytes((value + 128,))

    bits = sample_width_bytes * 8
    lower = -(2 ** (bits - 1))
    upper = (2 ** (bits - 1)) - 1
    if not lower <= value <= upper:
        raise ValueError(f"{bits}-bit fixture sample is out of range")
    return value.to_bytes(sample_width_bytes, byteorder="little", signed=True)
