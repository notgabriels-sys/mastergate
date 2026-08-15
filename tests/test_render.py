from __future__ import annotations

from pathlib import Path

from mastergate.check import check_batch
from mastergate.models import AudioFormat, BatchCheck, Delivery, DeliveryContract, Limits
from mastergate.render import (
    BLOCKED_VERDICT,
    INCOMPLETE_VERDICT,
    READY_FILE_CHECK,
    render_evidence_html,
)

from .helpers import write_pcm_wav


def test_render_evidence_html_shows_measured_facts_and_qc_boundary(tmp_path: Path) -> None:
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    write_pcm_wav(
        input_directory / "01-opening.wav",
        sample_width_bytes=3,
        channels=2,
        frames=((0, 0), (4194304, -4194304)),
    )
    batch = check_batch(_contract(("01-opening.wav",)), input_directory)

    evidence_html = render_evidence_html(batch)

    assert evidence_html.startswith("<!doctype html>")
    assert READY_FILE_CHECK in evidence_html
    assert INCOMPLETE_VERDICT in evidence_html
    assert "01-opening.wav" in evidence_html
    assert "48,000 Hz" in evidence_html
    assert "not a true-peak, loudness, listening, source-integrity, upload, or recipient-acceptance verification" in evidence_html
    assert str(input_directory) not in evidence_html
    assert "http://" not in evidence_html
    assert "https://" not in evidence_html
    assert "<script" not in evidence_html


def test_render_evidence_html_escapes_delivery_metadata_and_filename(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    filename = "01-<unsafe>&.wav"
    write_pcm_wav(input_directory / filename, sample_width_bytes=3, channels=2)
    contract = _contract(
        (filename,),
        title='Delivery <script>alert(1)</script> & "quoted"',
        requirements_basis="Basis <strong>not markup</strong> & more",
    )
    batch = check_batch(contract, input_directory)

    evidence_html = render_evidence_html(batch)

    assert "Delivery &lt;script&gt;alert(1)&lt;/script&gt; &amp; &quot;quoted&quot;" in evidence_html
    assert "Basis &lt;strong&gt;not markup&lt;/strong&gt; &amp; more" in evidence_html
    assert "01-&lt;unsafe&gt;&amp;.wav" in evidence_html
    assert "<script>alert(1)</script>" not in evidence_html
    assert "<strong>not markup</strong>" not in evidence_html


def test_render_evidence_html_escapes_blocking_errors(tmp_path: Path) -> None:
    raw_error = 'missing <script>alert("x")</script> & "unsafe" WAV file'
    batch = BatchCheck(
        contract=_contract(("01-opening.wav",)),
        input_directory=tmp_path / "input",
        measurements=(),
        errors=(raw_error,),
    )

    evidence_html = render_evidence_html(batch)

    assert BLOCKED_VERDICT in evidence_html
    assert "missing &lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; &quot;unsafe&quot; WAV file" in evidence_html
    assert raw_error not in evidence_html


def _contract(
    expected_files: tuple[str, ...],
    *,
    title: str = "Example WAV delivery",
    requirements_basis: str = "Provisional local contract - confirm with recipient.",
) -> DeliveryContract:
    return DeliveryContract(
        delivery=Delivery(title=title, requirements_basis=requirements_basis),
        audio_format=AudioFormat(sample_rate_hz=48000, bit_depth=24, channels=2),
        expected_files=expected_files,
        limits=Limits(max_sample_peak_dbfs=-1.0, reject_full_scale_samples=True),
    )
