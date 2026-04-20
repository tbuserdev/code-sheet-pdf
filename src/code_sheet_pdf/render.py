from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from pygments import lex
from pygments.lexers import CLexer
from pygments.token import Token
from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

FONT_PATH = Path("/System/Library/Fonts/Supplemental/Courier New.ttf")
FONT_NAME = "Courier New"
FONT_SIZE = 10
MIN_LINE_HEIGHT = 11
MAX_LINE_HEIGHT = FONT_SIZE * 1.75
MARGIN_MM = 7.5
COLUMN_GAP_MM = 5
GITHUB_LIGHT_DEFAULT_BG = HexColor("#ffffff")
GITHUB_LIGHT_DEFAULT_FG = HexColor("#1f2328")
GITHUB_LIGHT_DEFAULT_KEYWORD = HexColor("#cf222e")
GITHUB_LIGHT_DEFAULT_KEYWORD_TYPE = HexColor("#953800")
GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT = HexColor("#0550ae")
GITHUB_LIGHT_DEFAULT_FUNCTION = HexColor("#8250df")
GITHUB_LIGHT_DEFAULT_STRING = HexColor("#0a3069")
GITHUB_LIGHT_DEFAULT_NUMBER = HexColor("#0550ae")
GITHUB_LIGHT_DEFAULT_COMMENT = HexColor("#6e7781")
GITHUB_LIGHT_DEFAULT_OPERATOR = HexColor("#cf222e")
GITHUB_LIGHT_DEFAULT_PREPROC = HexColor("#cf222e")
GITHUB_LIGHT_DEFAULT_GENERIC_INSERTED = HexColor("#116329")
GITHUB_LIGHT_DEFAULT_GENERIC_DELETED = HexColor("#82071e")
GITHUB_LIGHT_DEFAULT_GENERIC_OUTPUT = HexColor("#0a3069")
GITHUB_LIGHT_DEFAULT_PUNCTUATION = HexColor("#1f2328")
BRACKET_COLORS = [
    HexColor("#0550ae"),
    HexColor("#8250df"),
    HexColor("#116329"),
    HexColor("#cf222e"),
    HexColor("#953800"),
    HexColor("#1b7c83"),
]

TOKEN_COLOR_MAP: dict[object, HexColor] = {
    Token.Text: GITHUB_LIGHT_DEFAULT_FG,
    Token.Text.Whitespace: GITHUB_LIGHT_DEFAULT_FG,
    Token.Keyword: GITHUB_LIGHT_DEFAULT_KEYWORD,
    Token.Keyword.Constant: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Keyword.Type: GITHUB_LIGHT_DEFAULT_KEYWORD_TYPE,
    Token.Name.Attribute: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Builtin: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Class: GITHUB_LIGHT_DEFAULT_KEYWORD_TYPE,
    Token.Name.Constant: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Decorator: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Entity: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Exception: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Function: GITHUB_LIGHT_DEFAULT_FUNCTION,
    Token.Name.Label: GITHUB_LIGHT_DEFAULT_STRING,
    Token.Name.Property: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Name.Tag: GITHUB_LIGHT_DEFAULT_GENERIC_INSERTED,
    Token.Name.Variable.Class: GITHUB_LIGHT_DEFAULT_KEYWORD_TYPE,
    Token.Literal: GITHUB_LIGHT_DEFAULT_STRING,
    Token.Literal.String: GITHUB_LIGHT_DEFAULT_STRING,
    Token.Literal.String.Affix: GITHUB_LIGHT_DEFAULT_KEYWORD,
    Token.Literal.String.Backtick: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Literal.String.Interpol: GITHUB_LIGHT_DEFAULT_KEYWORD,
    Token.Literal.String.Regex: GITHUB_LIGHT_DEFAULT_STRING,
    Token.Literal.String.Symbol: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Literal.Number: GITHUB_LIGHT_DEFAULT_NUMBER,
    Token.Operator: GITHUB_LIGHT_DEFAULT_OPERATOR,
    Token.Operator.Word: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Comment: GITHUB_LIGHT_DEFAULT_COMMENT,
    Token.Comment.Preproc: GITHUB_LIGHT_DEFAULT_PREPROC,
    Token.Comment.PreprocFile: GITHUB_LIGHT_DEFAULT_STRING,
    Token.Generic.Deleted: GITHUB_LIGHT_DEFAULT_GENERIC_DELETED,
    Token.Generic.Emph: GITHUB_LIGHT_DEFAULT_FG,
    Token.Generic.Error: GITHUB_LIGHT_DEFAULT_GENERIC_DELETED,
    Token.Generic.Heading: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Generic.Inserted: GITHUB_LIGHT_DEFAULT_GENERIC_INSERTED,
    Token.Generic.Output: GITHUB_LIGHT_DEFAULT_GENERIC_OUTPUT,
    Token.Generic.Prompt: GITHUB_LIGHT_DEFAULT_KEYWORD,
    Token.Generic.Strong: GITHUB_LIGHT_DEFAULT_FG,
    Token.Generic.Subheading: GITHUB_LIGHT_DEFAULT_KEYWORD_CONSTANT,
    Token.Generic.EmphStrong: GITHUB_LIGHT_DEFAULT_FG,
    Token.Generic.Traceback: GITHUB_LIGHT_DEFAULT_GENERIC_DELETED,
    Token.Punctuation: GITHUB_LIGHT_DEFAULT_PUNCTUATION,
}


class ToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceColumn:
    path: Path
    code: str


@dataclass(frozen=True)
class TextRun:
    text: str
    color: HexColor | None


@dataclass
class BracketState:
    depth: int = 0


def render_pdf(input_files: list[Path] | tuple[Path, ...], output_file: Path) -> None:
    columns = [_read_source(path) for path in input_files]
    ensure_font()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output_file), pagesize=A4)
    canvas.setTitle("code-sheet-pdf")

    page_width, page_height = A4
    margin = MARGIN_MM * mm
    gap = COLUMN_GAP_MM * mm
    usable_width = page_width - (2 * margin) - (2 * gap)
    column_width = usable_width / 3
    max_chars = max(1, int(column_width // char_width()))
    wrapped_columns = [wrap_source(column.code, max_chars) for column in columns]
    max_lines = max(len(lines) for lines in wrapped_columns)
    max_lines_capacity = int(
        ((page_height - (2 * margin) - FONT_SIZE) // MIN_LINE_HEIGHT) + 1
    )
    if max_lines > max_lines_capacity:
        raise ToolError(
            f"Input needs {max_lines} lines, but page fits only {max_lines_capacity}."
        )
    line_height = compute_line_height(page_height, margin, max_lines)

    column_xs = [
        margin,
        margin + column_width + gap,
        margin + (2 * column_width) + (2 * gap),
    ]
    top_y = page_height - margin - FONT_SIZE

    for index, (column, lines) in enumerate(zip(columns, wrapped_columns, strict=True)):
        draw_column(canvas, column_xs[index], top_y, lines, line_height)

    canvas.showPage()
    canvas.save()


def compute_line_height(page_height: float, margin: float, max_lines: int) -> float:
    if max_lines <= 1:
        return MIN_LINE_HEIGHT
    usable_height = page_height - (2 * margin) - FONT_SIZE
    return min(MAX_LINE_HEIGHT, max(MIN_LINE_HEIGHT, usable_height / (max_lines - 1)))


def ensure_font() -> None:
    if not FONT_PATH.exists():
        raise ToolError(f"Missing required font: {FONT_PATH}")
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))


def char_width() -> float:
    ensure_font()
    return pdfmetrics.stringWidth("M", FONT_NAME, FONT_SIZE)


def draw_column(
    canvas: Canvas,
    x: float,
    top_y: float,
    lines: list[list[TextRun]],
    line_height: float,
) -> None:
    y = top_y
    for line in lines:
        draw_line(canvas, x, y, line)
        y -= line_height


def draw_line(canvas: Canvas, x: float, y: float, runs: list[TextRun]) -> None:
    cursor = x
    for run in runs:
        if not run.text:
            continue
        canvas.setFillColor(run.color or black)
        canvas.setFont(FONT_NAME, FONT_SIZE)
        canvas.drawString(cursor, y, run.text)
        cursor += pdfmetrics.stringWidth(run.text, FONT_NAME, FONT_SIZE)


def wrap_source(code: str, max_chars: int) -> list[list[TextRun]]:
    normalized = code.expandtabs(4).replace("\r\n", "\n").replace("\r", "\n")
    lines: list[list[TextRun]] = [[]]
    used_chars = 0
    bracket_state = BracketState()
    tokens = list(lex(normalized, CLexer()))

    for index, (token_type, value) in enumerate(tokens):
        token_color = token_style_color(
            token_type,
            is_function_call=is_function_call_token(tokens, index),
        )
        bracket_sensitive = is_bracket_sensitive(token_type)
        parts = value.split("\n")
        for part_index, part in enumerate(parts):
            if part:
                used_chars = append_wrapped_text(
                    lines,
                    used_chars,
                    part,
                    token_color,
                    max_chars,
                    bracket_state,
                    bracket_sensitive,
                )
            if part_index < len(parts) - 1:
                lines.append([])
                used_chars = 0

    if lines and not lines[-1]:
        lines.pop()
    return lines


def append_wrapped_text(
    lines: list[list[TextRun]],
    used_chars: int,
    text: str,
    color: HexColor | None,
    max_chars: int,
    bracket_state: BracketState,
    bracket_sensitive: bool,
) -> int:
    for ch in text:
        if used_chars == max_chars:
            lines.append([])
            used_chars = 0
        ch_color = color
        if bracket_sensitive:
            ch_color = bracket_color_for_char(ch, bracket_state) or color
        append_char(lines[-1], ch, ch_color)
        used_chars += 1
    return used_chars


def append_char(runs: list[TextRun], ch: str, color: HexColor | None) -> None:
    if runs and runs[-1].color == color:
        runs[-1] = TextRun(text=runs[-1].text + ch, color=color)
    else:
        runs.append(TextRun(text=ch, color=color))


def bracket_color_for_char(ch: str, bracket_state: BracketState) -> HexColor | None:
    if ch in BRACKET_OPENERS:
        color = BRACKET_COLORS[bracket_state.depth % len(BRACKET_COLORS)]
        bracket_state.depth += 1
        return color
    if ch in BRACKET_CLOSERS:
        if bracket_state.depth > 0:
            bracket_state.depth -= 1
        return BRACKET_COLORS[bracket_state.depth % len(BRACKET_COLORS)]
    return None


def is_bracket_sensitive(token_type) -> bool:
    current = token_type
    while current is not Token:
        if current in (Token.Comment, Token.Literal.String):
            return False
        current = current.parent
    return True


def is_function_call_token(tokens: list[tuple[object, str]], index: int) -> bool:
    token_type, _ = tokens[index]
    if token_type not in {Token.Name, Token.Name.Function}:
        return False

    for next_type, next_value in tokens[index + 1 :]:
        if next_type in {Token.Text, Token.Text.Whitespace}:
            continue
        return next_type is Token.Punctuation and next_value == "("
    return False


def token_style_color(token_type, *, is_function_call: bool = False) -> HexColor | None:
    if is_function_call and token_type in {Token.Name, Token.Name.Function}:
        return GITHUB_LIGHT_DEFAULT_FUNCTION
    current = token_type
    while current is not Token:
        color = TOKEN_COLOR_MAP.get(current)
        if color:
            return color
        current = current.parent
    return GITHUB_LIGHT_DEFAULT_FG


def _read_source(path: Path) -> SourceColumn:
    if not path.exists():
        raise ToolError(f"Missing input file: {path}")
    if not path.is_file():
        raise ToolError(f"Not a file: {path}")
    return SourceColumn(path=path, code=path.read_text(encoding="utf-8"))


def build_preview_html(input_files: list[Path] | tuple[Path, ...]) -> str:
    columns = [_read_source(path) for path in input_files]
    column_width = preview_column_width()
    wrapped_columns = [wrap_source(column.code, column_width) for column in columns]
    max_lines = max(len(lines) for lines in wrapped_columns)
    line_height = compute_line_height(A4[1], MARGIN_MM * mm, max_lines)
    rendered_columns = []
    for lines in wrapped_columns:
        rendered_columns.append(
            '<section class="column"><pre>'
            + "<br>".join(
                "".join(render_text_run(run) for run in line) for line in lines
            )
            + "</pre></section>"
        )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>code-sheet-pdf preview</title>
    <meta http-equiv="refresh" content="1">
    <style>
      {preview_css(line_height)}
    </style>
  </head>
  <body>
    <main class="page">
      {"".join(rendered_columns)}
    </main>
  </body>
</html>
"""


def preview_css(line_height: float) -> str:
    return f"""
      @font-face {{
        font-family: "{FONT_NAME}";
        src: url("{FONT_PATH.as_uri()}");
        font-style: normal;
        font-weight: 400;
      }}
      html, body {{
        margin: 0;
        padding: 0;
        background: {color_to_css(GITHUB_LIGHT_DEFAULT_BG)};
      }}
      body {{
        display: flex;
        justify-content: center;
        padding: 16px;
      }}
      .page {{
        width: 210mm;
        height: 297mm;
        box-sizing: border-box;
        padding: 7.5mm;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 5mm;
        background: #fff;
        color: {GITHUB_LIGHT_DEFAULT_FG};
        font-family: "{FONT_NAME}", monospace;
        font-size: 10pt;
        font-weight: 400;
        font-style: normal;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(31, 35, 40, 0.12);
      }}
      .column {{
        min-width: 0;
        overflow: hidden;
      }}
      pre {{
        margin: 0;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        word-break: break-word;
        line-height: {line_height:.3f}pt;
      }}
    """


def preview_column_width() -> int:
    page_width, _ = A4
    margin = MARGIN_MM * mm
    gap = COLUMN_GAP_MM * mm
    usable_width = page_width - (2 * margin) - (2 * gap)
    return max(1, int((usable_width / 3) // char_width()))


def render_text_run(run: TextRun) -> str:
    return f'<span style="color: {color_to_css(run.color)}">{escape(run.text)}</span>'


def color_to_css(color: HexColor | None) -> str:
    if color is None:
        return "#1f2328"
    return f"#{color.hexval()[2:]}"


BRACKET_OPENERS = "([{"
BRACKET_CLOSERS = ")]}"
