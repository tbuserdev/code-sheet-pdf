from pathlib import Path

import pytest

from code_sheet_pdf.cli import main


def test_cli_rejects_wrong_input_count(tmp_path: Path):
    one = tmp_path / "one.txt"
    one.write_text("int a;\n", encoding="utf-8")
    out = tmp_path / "out.pdf"
    with pytest.raises(SystemExit):
        main([str(one), "-o", str(out)])
