"""Portable evidence renderers for Mastergate batch checks."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

from .models import BatchCheck, WavMeasurement


READY_FILE_CHECK = "DECLARED FILE CHECKS PASSED"
INCOMPLETE_VERDICT = "RENDERED - QC INCOMPLETE"
BLOCKED_VERDICT = "BLOCKED - REQUIREMENTS OR MEDIA MISSING"


def render_report(batch: BatchCheck) -> str:
    """Render a readable result with explicit limits on what it proves."""

    contract = batch.contract
    lines = [
        f"# Mastergate report - {_markdown_cell(contract.delivery.title)}",
        "",
        "## Declared delivery contract",
        "",
        "| Field | Declared value |",
        "| --- | --- |",
        f"| Requirement basis | {_markdown_cell(contract.delivery.requirements_basis)} |",
        f"| Sample rate | {contract.audio_format.sample_rate_hz} Hz |",
        f"| Bit depth | {contract.audio_format.bit_depth} |",
        f"| Channels | {contract.audio_format.channels} |",
        f"| Expected WAV files | {len(contract.expected_files)} |",
        "",
        "## Measured PCM WAV files",
        "",
        "| File | Size | Frames | Duration | Sample peak | Boundary samples | SHA-256 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    lines.extend(_measurement_row(measurement) for measurement in batch.measurements)
    if not batch.measurements:
        lines.append("| No readable expected WAV files |  |  |  |  |  |  |")

    lines.extend(["", "## Declared file-check result", ""])
    if batch.is_passed:
        lines.extend(
            [
                READY_FILE_CHECK,
                "",
                "## Overall delivery verdict",
                "",
                INCOMPLETE_VERDICT,
                "",
                "The declared files passed this local file-level contract. This is not a true-peak, loudness, listening, source-integrity, upload, or recipient-acceptance verification.",
            ]
        )
    else:
        lines.extend([BLOCKED_VERDICT, "", "### Blocking findings", ""])
        lines.extend(f"- {_markdown_cell(error)}" for error in batch.errors)

    lines.extend(
        [
            "",
            "## Still unverified",
            "",
            "- Correct source/session, revisions, dependencies, and recall state.",
            "- Auditioning for clicks, dropouts, boundaries, tails, noise, and musical suitability.",
            "- Inter-sample true peak, integrated loudness, DC, phase, mono compatibility, and stem reconstruction.",
            "- Archive re-open, transfer, recipient receipt, platform processing, publication, and public access.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_evidence_html(batch: BatchCheck) -> str:
    """Render a portable offline evidence brief from a declared file check."""

    contract = batch.contract
    title = _html(contract.delivery.title)
    measurement_rows = "\n".join(
        _html_measurement_row(measurement) for measurement in batch.measurements
    )
    if not measurement_rows:
        measurement_rows = (
            '<tr><td colspan="7">No readable expected WAV files.</td></tr>'
        )

    contract_rows = "\n".join(
        (
            _html_definition_row("Requirement basis", contract.delivery.requirements_basis),
            _html_definition_row(
                "Declared format",
                " / ".join(
                    (
                        f"{contract.audio_format.sample_rate_hz:,} Hz",
                        f"{contract.audio_format.bit_depth}-bit",
                        f"{contract.audio_format.channels} channels",
                    )
                ),
            ),
            _html_definition_row("Expected WAV files", len(contract.expected_files)),
            _html_definition_row(
                "Declared sample-peak ceiling",
                _sample_peak_limit_text(contract.limits.max_sample_peak_dbfs),
            ),
            _html_definition_row(
                "Full-scale boundary samples",
                "Rejected" if contract.limits.reject_full_scale_samples else "Allowed",
            ),
        )
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mastergate evidence brief — {title}</title>
  <style>
    :root {{
      color: #171715;
      background: #ece9e1;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #ece9e1; }}
    main {{ max-width: 72rem; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    article {{ background: #fffefa; border: 1px solid #d4d0c5; box-shadow: 0 1rem 3rem rgba(23, 23, 21, 0.08); }}
    header, section, footer {{ padding: 1.5rem; }}
    header {{ background: #171715; color: #fffefa; }}
    h1, h2, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 0.45rem; font-size: clamp(1.8rem, 5vw, 3rem); letter-spacing: -0.04em; }}
    h2 {{ font-size: 1rem; letter-spacing: 0.08em; text-transform: uppercase; }}
    .eyebrow {{ color: #c7aa76; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }}
    .lede {{ max-width: 56rem; line-height: 1.55; }}
    .status {{ display: inline-block; margin-bottom: 0.7rem; padding: 0.45rem 0.65rem; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.08em; }}
    .status-pass {{ background: #dfeedd; color: #1e4a22; }}
    .status-blocked {{ background: #f7dddd; color: #6b1717; }}
    .verdict {{ margin-bottom: 0.65rem; font-size: 1.2rem; font-weight: 800; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ padding: 0.7rem; border-bottom: 1px solid #dcd8ce; text-align: left; vertical-align: top; }}
    th {{ background: #f3f0e9; font-size: 0.75rem; letter-spacing: 0.07em; text-transform: uppercase; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; overflow-wrap: anywhere; }}
    ul {{ padding-left: 1.2rem; line-height: 1.55; }}
    footer {{ border-top: 1px solid #dcd8ce; color: #56534d; font-size: 0.85rem; line-height: 1.5; }}
    @media print {{
      :root, body {{ background: #ffffff; }}
      main {{ max-width: none; padding: 0; }}
      article {{ border: 0; box-shadow: none; }}
      header, section, footer {{ padding: 1rem 0; }}
    }}
  </style>
</head>
<body>
  <main>
    <article>
      <header>
        <p class="eyebrow">Offline file-level evidence brief</p>
        <h1>{title}</h1>
        <p class="lede">Measured facts from one declared integer PCM WAV delivery contract. This brief supports review before handoff; it is not a release certificate.</p>
      </header>
      <section>
        <h2>Declared delivery contract</h2>
        <div class="table-wrap">
          <table>
            <tbody>
{contract_rows}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <h2>Measured PCM WAV files</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>File</th><th>Size</th><th>Frames</th><th>Duration</th><th>Sample peak</th><th>Boundary samples</th><th>SHA-256</th></tr>
            </thead>
            <tbody>
{measurement_rows}
            </tbody>
          </table>
        </div>
      </section>
      {_html_result_section(batch)}
      <section>
        <h2>Still unverified</h2>
        <ul>
          <li>Correct source/session, revisions, dependencies, and recall state.</li>
          <li>Auditioning for clicks, dropouts, boundaries, tails, noise, and musical suitability.</li>
          <li>Inter-sample true peak, integrated loudness, DC, phase, mono compatibility, and stem reconstruction.</li>
          <li>Archive re-open, transfer, recipient receipt, platform processing, publication, and public access.</li>
        </ul>
      </section>
      <footer>Generated locally from one declared file-level contract. It does not establish rights, approval, recipient acceptance, upload, publication, or public availability.</footer>
    </article>
  </main>
</body>
</html>
"""


def render_manifest(batch: BatchCheck, contract_source: Path) -> str:
    """Render machine-readable measured facts without absolute input paths."""

    contract = batch.contract
    manifest = {
        "contract": {
            "assets": {"expected_files": list(contract.expected_files)},
            "delivery": {
                "requirements_basis": contract.delivery.requirements_basis,
                "title": contract.delivery.title,
            },
            "format": {
                "bit_depth": contract.audio_format.bit_depth,
                "channels": contract.audio_format.channels,
                "sample_rate_hz": contract.audio_format.sample_rate_hz,
            },
            "limits": {
                "max_sample_peak_dbfs": contract.limits.max_sample_peak_dbfs,
                "reject_full_scale_samples": contract.limits.reject_full_scale_samples,
            },
        },
        "contract_source": {
            "filename": contract_source.name,
            "sha256": _sha256(contract_source),
        },
        "declared_file_checks_passed": batch.is_passed,
        "errors": list(batch.errors),
        "input": {"directory_name": batch.input_directory.name},
        "measurements": [
            measurement_to_dict(measurement) for measurement in batch.measurements
        ],
        "overall_delivery_verdict": (
            INCOMPLETE_VERDICT if batch.is_passed else BLOCKED_VERDICT
        ),
        "schema_version": 1,
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_checksums(batch: BatchCheck) -> str:
    """Render standard two-space-separated checksums for measured files."""

    return "".join(
        f"{measurement.sha256}  {measurement.path.name}\n"
        for measurement in batch.measurements
    )


def batch_to_dict(batch: BatchCheck) -> dict[str, object]:
    """Return the check result for the CLI JSON mode."""

    return {
        "declared_file_checks_passed": batch.is_passed,
        "errors": list(batch.errors),
        "measurements": [measurement_to_dict(measurement) for measurement in batch.measurements],
        "overall_delivery_verdict": (
            INCOMPLETE_VERDICT if batch.is_passed else BLOCKED_VERDICT
        ),
    }


def measurement_to_dict(measurement: WavMeasurement) -> dict[str, object]:
    """Use a filename only, preserving portability and avoiding host paths."""

    return {
        "bit_depth": measurement.bit_depth,
        "byte_size": measurement.byte_size,
        "channels": measurement.channels,
        "duration_seconds": measurement.duration_seconds,
        "filename": measurement.path.name,
        "frame_count": measurement.frame_count,
        "full_scale_sample_count": measurement.full_scale_sample_count,
        "sample_peak_dbfs": measurement.sample_peak_dbfs,
        "sample_rate_hz": measurement.sample_rate_hz,
        "sha256": measurement.sha256,
    }


def _measurement_row(measurement: WavMeasurement) -> str:
    return "| {filename} | {size} | {frames} | {duration:.6f} s | {peak} | {boundaries} | `{sha256}` |".format(
        filename=_markdown_cell(measurement.path.name),
        size=measurement.byte_size,
        frames=measurement.frame_count,
        duration=measurement.duration_seconds,
        peak=_sample_peak_text(measurement.sample_peak_dbfs),
        boundaries=measurement.full_scale_sample_count,
        sha256=measurement.sha256,
    )


def _html_definition_row(label: str, value: object) -> str:
    return f"              <tr><th>{_html(label)}</th><td>{_html(value)}</td></tr>"


def _html_measurement_row(measurement: WavMeasurement) -> str:
    return "\n".join(
        (
            "              <tr>",
            f'                <td class="mono">{_html(measurement.path.name)}</td>',
            f"                <td>{_html(f'{measurement.byte_size:,} bytes')}</td>",
            f"                <td>{_html(f'{measurement.frame_count:,}')}</td>",
            f"                <td>{_html(f'{measurement.duration_seconds:.6f} s')}</td>",
            f"                <td>{_html(_sample_peak_text(measurement.sample_peak_dbfs))}</td>",
            f"                <td>{_html(measurement.full_scale_sample_count)}</td>",
            f'                <td class="mono">{_html(measurement.sha256)}</td>',
            "              </tr>",
        )
    )


def _html_result_section(batch: BatchCheck) -> str:
    if batch.is_passed:
        return f"""<section>
        <p class="status status-pass">{_html(READY_FILE_CHECK)}</p>
        <h2>Overall delivery verdict</h2>
        <p class="verdict">{_html(INCOMPLETE_VERDICT)}</p>
        <p class="lede">The declared files passed this local file-level contract. This is not a true-peak, loudness, listening, source-integrity, upload, or recipient-acceptance verification.</p>
      </section>"""

    errors = "\n".join(f"          <li>{_html(error)}</li>" for error in batch.errors)
    if not errors:
        errors = "          <li>No blocking findings returned.</li>"
    return f"""<section>
        <p class="status status-blocked">{_html(BLOCKED_VERDICT)}</p>
        <h2>Blocking findings</h2>
        <ul>
{errors}
        </ul>
      </section>"""


def _sample_peak_limit_text(value: float | None) -> str:
    if value is None:
        return "Not declared"
    return f"{value:.2f} dBFS (sample)"


def _sample_peak_text(value: float | None) -> str:
    if value is None:
        return "digital silence"
    display = 0.0 if abs(value) < 0.005 else value
    return f"{display:.2f} dBFS (sample)"


def _html(value: object) -> str:
    return html.escape(str(value), quote=True)


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _sha256(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
