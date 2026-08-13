from __future__ import annotations

from mastergate.check import check_batch
from mastergate.models import AudioFormat, Delivery, DeliveryContract, Limits

from .helpers import write_pcm_wav


def test_check_batch_accepts_matching_declared_pcm_wav_files(tmp_path) -> None:
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(input_directory / "01-opening.wav", frames=((0, 0), (8192, -8192)))
    write_pcm_wav(input_directory / "02-closing.wav", frames=((0, 0), (4096, -4096)))

    result = check_batch(
        _contract(("01-opening.wav", "02-closing.wav")), input_directory
    )

    assert result.is_passed
    assert result.errors == ()
    assert [measurement.path.name for measurement in result.measurements] == [
        "01-opening.wav",
        "02-closing.wav",
    ]


def test_check_batch_reports_missing_extra_and_contract_mismatches(tmp_path) -> None:
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(
        input_directory / "01-opening.wav",
        sample_rate_hz=44100,
        sample_width_bytes=2,
        channels=1,
        frames=((32767,),),
    )
    write_pcm_wav(input_directory / "03-unexpected.wav", channels=2)

    result = check_batch(
        _contract(("01-opening.wav", "02-closing.wav")), input_directory
    )

    assert not result.is_passed
    assert result.errors == (
        "missing expected WAV file: '02-closing.wav'",
        "unexpected WAV file: '03-unexpected.wav'",
        "01-opening.wav: sample rate is 44100 Hz; expected 48000 Hz",
        "01-opening.wav: bit depth is 16; expected 24",
        "01-opening.wav: channels is 1; expected 2",
        "01-opening.wav: sample peak 0.00 dBFS exceeds declared maximum -1.00 dBFS",
        "01-opening.wav: contains 1 full-scale boundary sample(s), which the contract rejects",
    )


def _contract(expected_files: tuple[str, ...]) -> DeliveryContract:
    return DeliveryContract(
        delivery=Delivery(
            title="Example WAV delivery",
            requirements_basis="Provisional local contract - confirm with recipient.",
        ),
        audio_format=AudioFormat(sample_rate_hz=48000, bit_depth=24, channels=2),
        expected_files=expected_files,
        limits=Limits(max_sample_peak_dbfs=-1.0, reject_full_scale_samples=True),
    )
