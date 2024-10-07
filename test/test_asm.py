from pathlib import Path
from unittest.mock import patch

import pytest

from whitespace_asm import asm


@pytest.mark.parametrize(
    "input_filename,option,output_filename,expected_output_filename",
    [
        pytest.param("input.wsasm", "-o", "output.ws", "output.ws", id="input-o"),
        pytest.param("input2.wsasm", "--out", "output.ws", "output.ws", id="input-out"),
        pytest.param("hello-world.wsasm", "", "", "hello-world.ws", id="input-only"),
    ],
)
def test_main(
    mock_assemble,
    input_filename: str,
    option: str,
    output_filename: str,
    expected_output_filename: str,
    in_temp_dir: Path,
):
    mock_assemble.return_value = ("Some output", [])

    (in_temp_dir / input_filename).write_text("Some input", encoding="utf-8")

    args = [str(in_temp_dir / input_filename)]
    if option:
        args += [option, str(in_temp_dir / output_filename)]

    asm.main(args)

    output_contents = (in_temp_dir / expected_output_filename).read_text(encoding="utf-8")
    assert output_contents == "Some output"


def test_main_with_errors(mock_assemble, in_temp_dir, capsys):
    mock_assemble.return_value = ("Something", ["4: Error1", "6: Error2"])

    (in_temp_dir / "file.wsasm").write_text("Some input", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        asm.main([str(in_temp_dir / "file.wsasm")])

    assert exc.value.code != 0
    assert not (in_temp_dir / "file.ws").exists()

    err = capsys.readouterr().err
    expected_errors = """\
4: Error1
6: Error2
"""
    assert expected_errors in err


@pytest.mark.parametrize(
    "line,expected_keyword,expected_param,expected_comment",
    [
        pytest.param("", "", "", "", id="empty-line"),
        pytest.param(" \t", "", "", "", id="whitespace-only"),
        pytest.param(
            " ;Output 'Hello, World!\\n' ", "", "", ";Output 'Hello, World!\\n'", id="comment-only"
        ),
        pytest.param("hello", "hello", "", "", id="keyword-only"),
        pytest.param(
            "whatever;This is a comment",
            "whatever",
            "",
            ";This is a comment",
            id="keyword-no-space-comment",
        ),
        pytest.param(
            "stuff ;This is a comment",
            "stuff",
            "",
            ";This is a comment",
            id="keyword-space-comment",
        ),
        pytest.param(
            "nonsense\t;My comment",
            "nonsense",
            "",
            ";My comment",
            id="keyword-tab-comment",
        ),
        pytest.param("push 1234", "push", "1234", "", id="keyword-num-param"),
        pytest.param("jump ''", "jump", "''", "", id="keyword-empty-char-param"),
        pytest.param("jump 'H'", "jump", "'H'", "", id="keyword-char-param"),
        pytest.param("jump ';'", "jump", "';'", "", id="keyword-semicolon-param"),
        pytest.param("push ' '", "push", "' '", "", id="keyword-space-param"),
        pytest.param("call '\\n'", "call", "'\\n'", "", id="keyword-newline-param"),
        pytest.param("jgt '\\''", "jgt", "'\\''", "", id="keyword-quote-param"),
        pytest.param("jeq 'ABC'", "jeq", "'ABC'", "", id="keyword-multichar-param"),
        pytest.param(
            "push 5555;hello", "push", "5555", ";hello", id="keyword-num-param-no-space-comment"
        ),
        pytest.param(
            "push 7654 hello",
            "push",
            "7654",
            ";hello",
            id="keyword-num-param-space-no-semicolon-comment",
        ),
        pytest.param(
            "push '\\t'What?",
            "push",
            "'\\t'",
            ";What?",
            id="keyword-char-param-no-semicolon-comment",
        ),
        pytest.param(
            "push 'x' That",
            "push",
            "'x'",
            ";That",
            id="keyword-char-param-no-semicolon-space-comment",
        ),
        pytest.param(
            "push '4'\thello?",
            "push",
            "'4'",
            ";hello?",
            id="keyword-char-param-no-semicolon-tab-comment",
        ),
        pytest.param(
            "xyz 'x';comment",
            "xyz",
            "'x'",
            ";comment",
            id="keyword-char-param-semicolon-no-space-comment",
        ),
        pytest.param(
            "zyx '' this is a comment",
            "zyx",
            "''",
            ";this is a comment",
            id="keyword-empty-char-parameter-no-semicolon-comment",
        ),
    ],
)
def test_parse_line(line: str, expected_keyword: str, expected_param: str, expected_comment: str):
    parsed_line = asm.parse_line(line)

    assert parsed_line.keyword == expected_keyword
    assert parsed_line.param == expected_param
    assert parsed_line.comment == expected_comment


@pytest.mark.parametrize(
    "param,expected_result",
    [
        pytest.param("12345", 12345, id="positive-int"),
        pytest.param("-571", -571, id="negative-int"),
        pytest.param("1.2", None, id="positive-float"),
        pytest.param("-3.14", None, id="negative-float"),
        pytest.param("'x'", None, id="string"),
    ],
)
def test_parse_number(param: str, expected_result: int | None):
    result = asm.parse_number(param)

    assert result == expected_result


@pytest.mark.parametrize(
    "param,expected_result",
    [
        pytest.param("'A'", "A", id="single-char"),
        pytest.param("'\\n'", "\n", id="newline"),
        pytest.param("'\\t'", "\t", id="tab"),
        pytest.param("'abcde'", "abcde", id="multi-char"),
        pytest.param("42", None, id="positive-int"),
        pytest.param("-53", None, id="negative-int"),
        pytest.param("3.14", None, id="positive-float"),
        pytest.param("-2.818", None, id="negative-float"),
        pytest.param("'a", None, id="unterminate-char"),
    ],
)
def test_parse_string(param: str, expected_result: str | None):
    result = asm.parse_string(param)

    assert result == expected_result


@pytest.mark.parametrize(
    "param,param_type,expected_result",
    [
        pytest.param("5733", asm.WhitespaceParamType.NUMBER, 5733, id="positive-int-number"),
        pytest.param("-40", asm.WhitespaceParamType.NUMBER, -40, id="negative-int-number"),
        pytest.param("1021", asm.WhitespaceParamType.VALUE, 1021, id="positive-int-value"),
        pytest.param("-987", asm.WhitespaceParamType.VALUE, -987, id="negative-int-value"),
        pytest.param("75", asm.WhitespaceParamType.LABEL, 75, id="positive-int-label"),
        pytest.param("-7656", asm.WhitespaceParamType.LABEL, -7656, id="negative-int-label"),
    ],
)
def test_parse_param_when_number_for_number_value_label(
    param: str, param_type: asm.ParserError, expected_result: int
):
    result = asm.parse_param(param, param_type)

    assert result == expected_result


@pytest.mark.parametrize(
    "param,param_type,expected_result",
    [
        pytest.param("'A'", asm.WhitespaceParamType.VALUE, "A", id="char-value"),
        pytest.param("'\\n'", asm.WhitespaceParamType.VALUE, "\n", id="newline-value"),
        pytest.param("'B'", asm.WhitespaceParamType.VALUE, "B", id="char-label"),
        pytest.param("'\\t'", asm.WhitespaceParamType.LABEL, "\t", id="char-tab-label"),
        pytest.param("'HELLO'", asm.WhitespaceParamType.LABEL, "HELLO", id="multi-char-label"),
    ],
)
def test_parse_param_when_char_for_value_label(
    param: str, param_type: asm.WhitespaceParamType, expected_result: str
):
    result = asm.parse_param(param, param_type)

    assert result == expected_result


@pytest.mark.parametrize(
    "comment,expected_comment",
    [
        pytest.param(";no", ";no_", id="no-space"),
        pytest.param("; This is a comment", ";_This_is_a_comment_", id="no-trailing space"),
        pytest.param(";hi, there ", ";hi,_there_", id="trailing-space"),
        pytest.param("; output ' '", ";_output_'<space>'_", id="space-char"),
        pytest.param(
            "; Output 'Hello, World, and welcome!'",
            ";_Output_'Hello,_World,_and_welcome!'_",
            id="space-string",
        ),
    ],
)
def test_format_comment(comment, expected_comment):
    assert asm.format_comment(comment) == expected_comment


@pytest.fixture()
def mock_assemble():
    with patch("whitespace_asm.asm.assemble") as mock:
        yield mock
