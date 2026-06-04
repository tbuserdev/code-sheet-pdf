from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .preview import serve_preview
from .render import COLUMNS_PER_PAGE, ToolError, render_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code-sheet-pdf",
        description=(
            "Render text files as highlighted A4 PDF pages with three columns per page."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        metavar="SOURCE",
        help=(
            f"Source files in groups of {COLUMNS_PER_PAGE}; "
            f"for example, {COLUMNS_PER_PAGE * 2} files render as two pages."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output PDF path.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open browser preview with auto-refresh.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.preview:
            serve_preview(args.inputs, args.output)
        else:
            render_pdf(args.inputs, args.output)
    except ToolError as exc:
        parser.error(str(exc))
    return 0
