"""Command-line interface for Mastergate's local PCM WAV preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .build import OutputDirectoryExistsError, build_evidence_files
from .check import InputDirectoryError, check_batch
from .contract import ContractFormatError, validate_contract, load_contract
from .render import (
    BLOCKED_VERDICT,
    INCOMPLETE_VERDICT,
    READY_FILE_CHECK,
    batch_to_dict,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run a read-only check or build evidence from a passing check."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        contract = load_contract(arguments.contract_file)
    except ContractFormatError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    contract_report = validate_contract(contract)
    if not contract_report.is_valid:
        for error in contract_report.errors:
            print(f"INVALID CONTRACT: {error}", file=sys.stderr)
        return 1

    try:
        batch = check_batch(contract, arguments.input_directory)
    except InputDirectoryError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if arguments.command == "check":
        return _run_check(batch, as_json=arguments.json)

    if not batch.is_passed:
        _print_blocking_errors(batch.errors)
        return 1

    try:
        result = build_evidence_files(batch, arguments.contract_file, arguments.output)
    except OutputDirectoryExistsError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"Built Mastergate evidence files: {result.output}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mastergate",
        description="Check a declared PCM WAV batch without changing the source audio.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    check_parser = subcommands.add_parser("check", help="read-only WAV batch preflight")
    check_parser.add_argument("contract_file", type=Path)
    check_parser.add_argument("input_directory", type=Path)
    check_parser.add_argument("--json", action="store_true", help="emit measured result JSON")

    build_parser = subcommands.add_parser(
        "build", help="write evidence files only after a passing declared file check"
    )
    build_parser.add_argument("contract_file", type=Path)
    build_parser.add_argument("input_directory", type=Path)
    build_parser.add_argument("--output", type=Path, required=True)
    return parser


def _run_check(batch, *, as_json: bool) -> int:
    if as_json:
        print(json.dumps(batch_to_dict(batch), ensure_ascii=False, sort_keys=True))
    elif batch.is_passed:
        count = len(batch.measurements)
        noun = "WAV file" if count == 1 else "WAV files"
        print(f"{READY_FILE_CHECK} ({count} {noun}).")
        print(f"Overall delivery verdict: {INCOMPLETE_VERDICT}.")
    else:
        _print_blocking_errors(batch.errors)
    return 0 if batch.is_passed else 1


def _print_blocking_errors(errors: tuple[str, ...]) -> None:
    print(BLOCKED_VERDICT, file=sys.stderr)
    for error in errors:
        print(f"BLOCKED: {error}", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - exercised by installed command smoke test.
    raise SystemExit(main())
