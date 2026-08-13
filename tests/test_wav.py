from __future__ import annotations

import math

from mastergate.wav import inspect_wav

from .helpers import write_pcm_wav


def test_inspect_wav_measures_pcm_header_duration_and_sample_peak(tmp_path) -> None:
    source = write_pcm_wav(
        tmp_path / "half-scale.wav",
        sample_rate_hz=48000,
        sample_width_bytes=2,
        channels=2,
        frames=((0, 0), (16384, -16384), (0, 0)),
    )

    measurement = inspect_wav(source)

    assert measurement.path == source
    assert measurement.byte_size > 0
    assert len(measurement.sha256) == 64
    assert measurement.sample_rate_hz == 48000
    assert measurement.bit_depth == 16
    assert measurement.channels == 2
    assert measurement.frame_count == 3
    assert measurement.duration_seconds == 3 / 48000
    assert math.isclose(measurement.sample_peak_dbfs, -6.020599913, abs_tol=0.000001)
    assert measurement.full_scale_sample_count == 0


def test_inspect_wav_counts_full_scale_boundary_samples(tmp_path) -> None:
    source = write_pcm_wav(
        tmp_path / "boundary.wav",
        sample_width_bytes=2,
        channels=1,
        frames=((32767,), (-32768,), (0,)),
    )

    measurement = inspect_wav(source)

    assert measurement.sample_peak_dbfs == 0.0
    assert measurement.full_scale_sample_count == 2
