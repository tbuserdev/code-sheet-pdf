from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from pygments.token import Token

from code_sheet_pdf.render import (
    COLUMN_GAP_MM,
    FONT_NAME,
    FONT_SIZE,
    MAX_LINE_HEIGHT,
    MARGIN_MM,
    build_preview_html,
    compute_line_height,
    render_pdf,
    token_style_color,
    wrap_source,
)


def test_layout_constants_match_spec():
    assert MARGIN_MM == 7.5
    assert COLUMN_GAP_MM == 5
    assert FONT_NAME == "Courier New"
    assert FONT_SIZE == 10
    assert MAX_LINE_HEIGHT == 17.5


def test_compute_line_height_caps_at_max():
    assert compute_line_height(A4[1], 7.5 * mm, 4) == 17.5


def test_wrap_source_keeps_c_highlighting_tokens():
    lines = wrap_source("int main(void) { return 0; }\n", 80)
    assert lines
    assert any(run.text.strip() == "int" for run in lines[0])
    assert any(run.text.strip() == "return" for run in lines[0])
    assert token_style_color(Token.Keyword.Type) == HexColor("#953800")
    assert token_style_color(Token.Keyword) == HexColor("#cf222e")


def test_wrap_source_highlights_function_calls_like_vscode():
    lines = wrap_source("int fd = open(path, mode);\nperror(\"open\");\n", 80)
    colors = {
        run.text: run.color.hexval()
        for line in lines
        for run in line
        if run.text.strip() in {"open", "perror"}
    }
    assert colors["open"] == "0x8250df"
    assert colors["perror"] == "0x8250df"


def test_wrap_source_colors_nested_brackets_by_depth():
    lines = wrap_source("({[x]})\n", 80)
    bracket_runs = [
        (char, run.color.hexval())
        for line in lines
        for run in line
        for char in run.text
        if char in "()[]{}"
    ]
    assert bracket_runs == [
        ("(", "0x0550ae"),
        ("{", "0x8250df"),
        ("[", "0x116329"),
        ("]", "0x116329"),
        ("}", "0x8250df"),
        (")", "0x0550ae"),
    ]


def test_render_pdf_creates_single_page(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.txt"
    a.write_text("int alpha = 1;\nreturn alpha;\n", encoding="utf-8")
    b.write_text("int beta = 2;\nreturn beta;\n", encoding="utf-8")
    c.write_text("int gamma = 3;\nreturn gamma;\n", encoding="utf-8")

    out = tmp_path / "out" / "code-sheet-pdf.pdf"
    render_pdf([a, b, c], out)

    reader = PdfReader(str(out))
    assert len(reader.pages) == 1


def test_preview_html_refreshes(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.txt"
    a.write_text("int alpha = 1;\n", encoding="utf-8")
    b.write_text("int beta = 2;\n", encoding="utf-8")
    c.write_text("int gamma = 3;\n", encoding="utf-8")

    html = build_preview_html([a, b, c])
    assert 'meta http-equiv="refresh" content="1"' in html
    assert 'style="color: #953800">int</span>' in html
    assert 'style="color: #0550ae">1</span>' in html
