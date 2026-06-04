# code-sheet-pdf

Create compact A4 PDF pages from source files.

`code-sheet-pdf` is a small command-line tool for turning code snippets into a print-friendly PDF with three highlighted columns per page. It is useful for cheat sheets, exam notes, handouts, and any situation where a dense but readable code sheet matters.

## Features

- A4 PDF output
- Three source columns per page
- Multiple pages from inputs in groups of three
- C syntax highlighting with GitHub-style colors
- Fixed Courier New layout
- Automatic line wrapping per column
- Browser preview with auto-refresh
- No code execution

## Requirements

- Python 3.11 or newer
- `uv` for local development
- macOS with Courier New available at `/System/Library/Fonts/Supplemental/Courier New.ttf`

The current renderer requires that Courier New font path. Cross-platform font discovery is not implemented yet.

## Install

From a local checkout:

```bash
uv sync
```

## Usage

Render three files into a one-page PDF:

```bash
uv run code-sheet-pdf examples/col1.txt examples/col2.txt examples/col3.txt -o output/pdf/code-sheet-pdf.pdf
```

Render six files into a two-page PDF:

```bash
uv run code-sheet-pdf page1-col1.txt page1-col2.txt page1-col3.txt page2-col1.txt page2-col2.txt page2-col3.txt -o output/pdf/code-sheet-pdf.pdf
```

Open a browser preview while writing:

```bash
uv run code-sheet-pdf examples/page1-col1.txt examples/page1-col2.txt examples/page1-col3.txt examples/page2-col1.txt examples/page2-col2.txt examples/page2-col3.txt -o output/pdf/code-sheet-pdf.pdf --preview
```

Run as a Python module:

```bash
uv run python -m code_sheet_pdf page1-col1.txt page1-col2.txt page1-col3.txt page2-col1.txt page2-col2.txt page2-col3.txt -o output/pdf/code-sheet-pdf.pdf
```

## CLI

```text
usage: code-sheet-pdf SOURCE [SOURCE ...] -o OUTPUT [--preview]
```

Arguments:

- `SOURCE [SOURCE ...]`: source text files in groups of three
- `-o, --output`: output PDF path
- `--preview`: open a local browser preview with auto-refresh

## Layout

The generated PDF uses:

- A4 page size
- 7.5 mm page margins
- 5 mm gap between columns
- 10 pt Courier New
- 11 pt minimum line height
- 17.5 pt maximum line height

If the wrapped content does not fit on one page, the command exits with an error instead of silently clipping the PDF.

## Limitations

- Highlighting currently targets C source code.
- The layout expects input files in groups of three.
- The font path is macOS-specific.

These limits are deliberate for the current version and keep output predictable.

## Development

Install runtime and test dependencies:

```bash
uv sync --extra test
```

Run tests:

```bash
uv run pytest
```

Build source and wheel distributions:

```bash
uv build
```

## Acknowledgements

This project was developed with assistance from GPT-5.4 and GPT-5.4-Mini.

## License

MIT. See [LICENSE](LICENSE).
