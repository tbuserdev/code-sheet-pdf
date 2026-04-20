from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .preview import serve_preview
from .render import ToolError, render_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code-sheet-pdf",
        description="Render three text files as a highlighted A4 PDF.",
    )
    parser.add_argument(
        "inputs",
        nargs=3,
        type=Path,
        metavar="SOURCE",
        help="Three source files.",
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
