"""Safe creation of evidence files from an already-passing batch check."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from .models import BatchCheck
from .render import (
    render_checksums,
    render_evidence_html,
    render_manifest,
    render_report,
)


class DeclaredFileCheckFailedError(ValueError):
    """Raised when a failed batch would be represented as a delivery package."""

    def __init__(self, batch: BatchCheck) -> None:
        self.batch = batch
        super().__init__("\n".join(batch.errors))


class OutputDirectoryExistsError(FileExistsError):
    """Raised instead of replacing an existing output path."""


@dataclass(frozen=True)
class BuildResult:
    """New portable evidence files from a passing declared check."""

    output: Path
    files: tuple[Path, ...]


def build_evidence_files(
    batch: BatchCheck, contract_source: str | Path, output: str | Path
) -> BuildResult:
    """Atomically build evidence only for a batch that passed its contract."""

    if not batch.is_passed:
        raise DeclaredFileCheckFailedError(batch)

    contract_path = Path(contract_source)
    output_path = Path(output)
    if output_path.exists():
        raise OutputDirectoryExistsError(
            f"refusing to replace existing output directory: {output_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = Path(
        tempfile.mkdtemp(prefix=f".{output_path.name}.", dir=output_path.parent)
    )
    filenames = (
        "MASTERGATE_REPORT.md",
        "MASTERGATE_EVIDENCE.html",
        "checksums.sha256",
        "manifest.json",
    )
    try:
        (temporary_path / "MASTERGATE_REPORT.md").write_text(
            render_report(batch), encoding="utf-8"
        )
        (temporary_path / "MASTERGATE_EVIDENCE.html").write_text(
            render_evidence_html(batch), encoding="utf-8"
        )
        (temporary_path / "checksums.sha256").write_text(
            render_checksums(batch), encoding="utf-8"
        )
        (temporary_path / "manifest.json").write_text(
            render_manifest(batch, contract_path), encoding="utf-8"
        )
        temporary_path.replace(output_path)
    except BaseException:
        shutil.rmtree(temporary_path, ignore_errors=True)
        raise

    return BuildResult(
        output=output_path,
        files=tuple(output_path / filename for filename in filenames),
    )
