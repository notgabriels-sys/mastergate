from __future__ import annotations

from mastergate.contract import load_contract, validate_contract
from mastergate.models import AudioFormat, Delivery, DeliveryContract, Limits


def test_load_contract_parses_a_declared_pcm_wav_delivery(write_contract) -> None:
    source = write_contract(
        """
[delivery]
title = "Example WAV delivery"
requirements_basis = "Provisional local contract - confirm with recipient."

[format]
sample_rate_hz = 48000
bit_depth = 24
channels = 2

[assets]
expected_files = ["01-opening.wav", "02-closing.wav"]

[limits]
max_sample_peak_dbfs = -1.0
reject_full_scale_samples = true
""".strip()
    )

    assert load_contract(source) == DeliveryContract(
        delivery=Delivery(
            title="Example WAV delivery",
            requirements_basis="Provisional local contract - confirm with recipient.",
        ),
        audio_format=AudioFormat(sample_rate_hz=48000, bit_depth=24, channels=2),
        expected_files=("01-opening.wav", "02-closing.wav"),
        limits=Limits(max_sample_peak_dbfs=-1.0, reject_full_scale_samples=True),
    )


def test_validate_contract_requires_concrete_and_portable_requirements() -> None:
    contract = DeliveryContract(
        delivery=Delivery(title="  ", requirements_basis=""),
        audio_format=AudioFormat(sample_rate_hz=0, bit_depth=20, channels=0),
        expected_files=("01-opening.wav", "01-OPENING.WAV", "folder/02.wav", "notes.txt"),
        limits=Limits(max_sample_peak_dbfs=0.1, reject_full_scale_samples=False),
    )

    assert validate_contract(contract).errors == (
        "delivery.title must not be blank",
        "delivery.requirements_basis must not be blank",
        "format.sample_rate_hz must be a positive integer",
        "format.bit_depth must be one of 8, 16, 24, 32",
        "format.channels must be a positive integer",
        "assets.expected_files contains duplicate names after case normalization: '01-opening.wav'",
        "assets.expected_files entries must be bare .wav filenames: 'folder/02.wav'",
        "assets.expected_files entries must be bare .wav filenames: 'notes.txt'",
        "limits.max_sample_peak_dbfs must be less than or equal to 0 dBFS",
    )


def test_validate_contract_requires_at_least_one_expected_file() -> None:
    contract = DeliveryContract(
        delivery=Delivery(title="Example WAV delivery", requirements_basis="Recipient brief"),
        audio_format=AudioFormat(sample_rate_hz=48000, bit_depth=24, channels=2),
        expected_files=(),
        limits=Limits(),
    )

    assert validate_contract(contract).errors == (
        "assets.expected_files must contain at least one WAV filename",
    )
