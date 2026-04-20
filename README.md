# code-sheet-pdf

Render three code-source files into one A4 PDF with syntax highlighting.

## Features

- One A4 page
- Three columns
- Fixed monospaced layout
- C syntax highlighting
- Browser preview with auto-refresh

## Install

```bash
uv sync
```

For tests:

```bash
uv sync --extra test
```

## Use

```bash
uv run code-sheet-pdf examples/col1.txt examples/col2.txt examples/col3.txt -o output/pdf/code-sheet-pdf.pdf
```

Preview mode:

```bash
uv run code-sheet-pdf examples/col1.txt examples/col2.txt examples/col3.txt -o output/pdf/code-sheet-pdf.pdf --preview
```

## Test

```bash
uv run pytest
```

## Build

```bash
uv build
```
