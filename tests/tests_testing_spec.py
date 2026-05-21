"""
Tests for dlc.testing.spec 
"""

from pathlib import Path

from dlc.parser.dig_parser import parse_dig_file
from dlc.testing.spec import (
    Token, TestRow, TestSpec, VariableBinding,
    _tokenize, parse_data_string, extract_test_specs, match_variables_to_io,
)


SAMPLES_DIR = Path(__file__).parent.parent / "data" / "sample_circuits"

def test_tokenize_plain_decimal():
    t = _tokenize("25")
    assert t.kind == "int" and t.value == 25 and t.raw == "25"


def test_tokenize_negative_decimal_without_parens():
    t = _tokenize("-5")
    assert t.kind == "int" and t.value == -5


def test_tokenize_hex_lowercase_prefix():
    t = _tokenize("0xCB126889")
    assert t.kind == "int" and t.value == 0xCB126889


def test_tokenize_hex_uppercase_prefix():
    t = _tokenize("0X7F0")
    assert t.kind == "int" and t.value == 0x7F0


def test_tokenize_binary():
    t = _tokenize("0b0110011")
    assert t.kind == "int" and t.value == 0b0110011 == 51


def test_tokenize_parens_negative():
    t = _tokenize("(-20)")
    assert t.kind == "int" and t.value == -20


def test_tokenize_parens_positive():
    t = _tokenize("(5)")
    assert t.kind == "int" and t.value == 5


def test_tokenize_clock_pulse_uppercase_only():
    assert _tokenize("C").kind == "clock"
    assert _tokenize("c").kind == "unknown"


def test_tokenize_highz_and_dontcare():
    assert _tokenize("z").kind == "highZ"
    assert _tokenize("Z").kind == "highZ"
    assert _tokenize("x").kind == "dontcare"
    assert _tokenize("X").kind == "dontcare"


def test_tokenize_loop_expressions():
    assert _tokenize("(N+1)").kind == "loop_expr"
    assert _tokenize("(N-60)").kind == "loop_expr"
    assert _tokenize("(N)").kind == "loop_expr"


def test_tokenize_unknown_is_recorded_not_raised():
    t = _tokenize("not-a-number")
    assert t.kind == "unknown" and t.value is None

def test_parse_data_string_single_and_pattern():
    text = "A B Y\n0 0 0\n0 1 0\n1 0 0\n1 1 1"
    headers, rows, has_loops = parse_data_string(text)
    assert headers == ["A", "B", "Y"]
    assert len(rows) == 4
    assert not has_loops
    assert rows[3].values[2].value == 1


def test_parse_data_string_strips_inline_comments():
    text = (
        "clk ReadData1 ReadData2\n"
        "0 0 0        # addi x4, x0, -20\n"
        "C (-20) 0    # addi x5, x4, 0x7F0\n"
    )
    headers, rows, has_loops = parse_data_string(text)
    assert headers == ["clk", "ReadData1", "ReadData2"]
    assert len(rows) == 2
    assert rows[1].values[0].kind == "clock"
    assert rows[1].values[1].value == -20
    assert not has_loops


def test_parse_data_string_skips_comment_only_lines_and_blanks():
    text = (
        "A B ALUOp Result FlagZ\n"
        "\n"
        "# ADD tests (ALUOp = 0b0010)\n"
        "0x289322C4 0x01846399 0b0010 0x2A17865D 0\n"
        "\n"
        "# SUB tests (ALUOp = 0b0110)\n"
        "0x39332544 0x0435FCAD 0b0110 0x34FD2897 0\n"
    )
    headers, rows, has_loops = parse_data_string(text)
    assert headers == ["A", "B", "ALUOp", "Result", "FlagZ"]
    assert len(rows) == 2
    assert rows[0].values[2].value == 0b0010
    assert rows[0].values[3].value == 0x2A17865D
    assert not has_loops


def test_parse_data_string_flags_loop_blocks():
    text = (
        "WriteReg WriteData RegWrite Clock\n"
        "loop(N, 30)\n"
        "(N+1) (N+1) 1 C\n"
        "end loop\n"
    )
    headers, rows, has_loops = parse_data_string(text)
    assert headers == ["WriteReg", "WriteData", "RegWrite", "Clock"]
    assert has_loops
    assert len(rows) == 1
    assert rows[0].values[0].kind == "loop_expr"
    assert rows[0].values[3].kind == "clock"


