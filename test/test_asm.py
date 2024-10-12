from pathlib import Path
from unittest.mock import patch

import pytest

from whitespace_asm import asm


@pytest.mark.parametrize(
    "input_filename,expected_output_filename",
    [
        pytest.param("input.wsasm", "input.ws", id="input-o"),
        pytest.param("input2.wsasm", "input2.ws", id="input-out"),
    ],
)
def test_main_with_defaults(
    mock_assemble,
    input_filename: str,
    expected_output_filename: str,
    in_temp_dir: Path,
):
    mock_assemble.return_value = ("Some output", [])

    input_path = in_temp_dir / input_filename
    input_path.write_text("Some input", encoding="utf-8")

    asm.main([str(input_path)])

    output_path = in_temp_dir / expected_output_filename
    output_contents = output_path.read_text(encoding="utf-8")
    assert output_contents == "Some output"

    mock_assemble.assert_called_once_with("Some input", "mark")


@pytest.mark.parametrize(
    "option,output_filename", [("-o", "output1.ws"), ("--output", "output2.ws")]
)
def test_main_with_output(mock_assemble, option: str, output_filename: str, in_temp_dir: Path):
    mock_assemble.return_value = ("This output", [])

    input_path = in_temp_dir / "this-file.wsasm"
    input_path.write_text("This input", encoding="utf-8")

    output_path = in_temp_dir / output_filename
    asm.main([str(input_path), option, str(output_path)])

    output_contents = output_path.read_text(encoding="utf-8")
    assert output_contents == "This output"

    mock_assemble.assert_called_once_with("This input", "mark")


@pytest.mark.parametrize("option,format_type", [("-f", "raw"), ("--format", "mark")])
def test_main_with_mark(mock_assemble, option: str, format_type: str, in_temp_dir: Path):
    mock_assemble.return_value = ("My output", [])

    input_path = in_temp_dir / "my-file.wsasm"
    input_path.write_text("My input", encoding="utf-8")

    asm.main([str(input_path), option, format_type])

    output_path = in_temp_dir / "my-file.ws"
    output_contents = output_path.read_text(encoding="utf-8")
    assert output_contents == "My output"

    mock_assemble.assert_called_once_with("My input", format_type)


def test_main_with_errors(mock_assemble, in_temp_dir, capsys):
    mock_assemble.return_value = ("Something", ["4: Error1", "6: Error2"])

    input_path = in_temp_dir / "file.wsasm"
    input_path.write_text("Some input", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        asm.main([str(input_path)])

    assert exc.value.code != 0
    assert not (in_temp_dir / "file.ws").exists()

    err = capsys.readouterr().err
    expected_errors = """\
4: Error1
6: Error2
"""
    assert expected_errors in err

    mock_assemble.assert_called_once_with("Some input", "mark")


@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        pytest.param("", [], id="empty-line"),
        pytest.param(" \t", [], id="whitespace-only"),
        pytest.param(
            " ;Output 'Hello, World!\\n' ", [";Output 'Hello, World!\\n'"], id="comment-only"
        ),
        pytest.param("hello", ["hello"], id="keyword-only"),
        pytest.param(
            "whatever;This is a comment",
            ["whatever", ";This is a comment"],
            id="keyword-no-space-comment",
        ),
        pytest.param(
            "stuff ;This is a comment",
            ["stuff", ";This is a comment"],
            id="keyword-space-comment",
        ),
        pytest.param(
            "nonsense\t;My comment",
            ["nonsense", ";My comment"],
            id="keyword-tab-comment",
        ),
        pytest.param("copy 1234", ["copy", "1234"], id="key-num-param"),
        pytest.param("push ''", ["push", "''"], id="keyword-empty-char-param"),
        pytest.param("push 'H'", ["push", "'H'"], id="keyword-char-param"),
        pytest.param(
            "push ';'",
            ["push", "';'"],
            id="keyword-semicolon-param",
        ),
        pytest.param("push ' '", ["push", "' '"], id="keyword-space-param"),
        pytest.param("push '\\n'", ["push", "'\\n'"], id="keyword-newline-param"),
        pytest.param("push '\\''", ["push", "'\\''"], id="keyword-quote-param"),
        pytest.param("push 'ABC'", ["push", "'ABC'"], id="keyword-multichar-param"),
        pytest.param(
            "push 5555;hello", ["push", "5555", ";hello"], id="keyword-num-param-no-space-comment"
        ),
        pytest.param(
            "push 7654 hello", ["push", "7654", "hello"], id="keyword-num-param-invalid-param"
        ),
        pytest.param(
            "push '\\t'What?",
            ["push", "'\\t'What?"],
            id="keyword-tab-extra-test-param",
        ),
        pytest.param(
            "push 'x' That",
            ["push", "'x'", "That"],
            id="keyword-char-param-invalid-param",
        ),
        pytest.param(
            "push '4'\thello?",
            ["push", "'4'", "hello?"],
            id="keyword-char-param-tab-invalid-param",
        ),
        pytest.param(
            "xyz 'x';comment",
            ["xyz", "'x'", ";comment"],
            id="keyword-char-param-semicolon-no-space-comment",
        ),
        pytest.param(
            "zyx '' this is junk",
            ["zyx", "''", "this", "is", "junk"],
            id="keyword-empty-char-parameter-extra-invalid-param",
        ),
        pytest.param("abc '", ["abc", "'"], id="keyword-unterm-char-param"),
    ],
)
def test_tokenize_line(line: str, expected_tokens: list[str]):
    tokens = asm.tokenize_line(line)

    assert tokens == expected_tokens


@pytest.mark.parametrize(
    "tokens,expected_keyword,expected_params,expected_comment",
    [
        pytest.param([], "", [], "", id="no-tokens"),
        pytest.param(["hello"], "hello", [], "", id="keyword-only"),
        pytest.param(["good", "bye"], "good", ["bye"], "", id="keyword-one-param"),
        pytest.param(
            ["stuff", "and", "nonsense"], "stuff", ["and", "nonsense"], "", id="keyword-two-params"
        ),
        pytest.param([";Some comment"], "", [], ";Some comment", id="comment-only"),
        pytest.param(
            ["xyz", ";This is a comment"], "xyz", [], ";This is a comment", id="keyword-comment"
        ),
    ],
)
def test_parse_tokens(tokens: list[str], expected_keyword, expected_params, expected_comment):
    command = asm.parse_tokens(tokens)

    assert command.keyword == expected_keyword
    assert command.params == expected_params
    assert command.comment == expected_comment


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
        pytest.param("Hello", None, id="invalid-string"),
    ],
)
def test_parse_string(param: str, expected_result: str | None):
    result = asm.parse_string(param)

    assert result == expected_result


@pytest.mark.parametrize(
    "param,expected_result",
    [
        pytest.param("0110", "0110", id="valid-binary"),
        pytest.param("1x0001", None, id="invalid-binary-letter"),
        pytest.param("1101211", None, id="invalid-binary-digit"),
    ],
)
def test_parse_label(param: str, expected_result: str | None):
    result = asm.parse_label(param)

    assert result == expected_result


@pytest.mark.parametrize(
    "param,param_type,expected_result,expected_error",
    [
        pytest.param("5733", asm.WhitespaceParamType.NUMBER, 5733, "", id="positive-int-number"),
        pytest.param("-40", asm.WhitespaceParamType.NUMBER, -40, "", id="negative-int-number"),
        pytest.param(
            "'b'",
            asm.WhitespaceParamType.NUMBER,
            None,
            "Expected number, but got 'b' instead",
            id="invalid-number",
        ),
        pytest.param("1021", asm.WhitespaceParamType.VALUE, 1021, "", id="positive-int-value"),
        pytest.param("-987", asm.WhitespaceParamType.VALUE, -987, "", id="negative-int-value"),
        pytest.param("'A'", asm.WhitespaceParamType.VALUE, "A", "", id="char-value"),
        pytest.param("'\\n'", asm.WhitespaceParamType.VALUE, "\n", "", id="newline-value"),
        pytest.param(
            "qwer",
            asm.WhitespaceParamType.VALUE,
            None,
            "Expected number or single character, but got qwer instead",
            id="invalid-value",
        ),
        pytest.param(
            "''",
            asm.WhitespaceParamType.VALUE,
            None,
            "Expected number or single character, but got '' instead",
            id="invalid-empty-value",
        ),
        pytest.param(
            "'AB'",
            asm.WhitespaceParamType.VALUE,
            None,
            "Expected number or single character, but got 'AB' instead",
            id="invalid-multi-char-value",
        ),
        pytest.param("10010110", asm.WhitespaceParamType.LABEL, "10010110", "", id="valid-label"),
        pytest.param(
            "10020110",
            asm.WhitespaceParamType.LABEL,
            None,
            "Expected zeros and ones, but got 10020110 instead",
            id="invalid-label-digits",
        ),
        pytest.param(
            "junk",
            asm.WhitespaceParamType.LABEL,
            None,
            "Expected zeros and ones, but got junk instead",
            id="invalid-label-letters",
        ),
    ],
)
def test_parse_param(
    param: str,
    param_type: asm.WhitespaceParamType,
    expected_result: int | str | None,
    expected_error: str,
):
    result, error = asm.parse_param(param, param_type)

    assert result == expected_result
    assert error == expected_error


def get_expected_result(result: str):
    return result.replace("S", asm.SPACE).replace("T", asm.TAB).replace("L", asm.LF)


@pytest.mark.parametrize(
    "param,param_type,expected_result",
    [
        pytest.param(
            75,
            asm.WhitespaceParamType.NUMBER,
            get_expected_result("STSSTSTTL"),
            id="num-positive-int",
        ),
        pytest.param(
            -123,
            asm.WhitespaceParamType.NUMBER,
            get_expected_result("TTTTTSTTL"),
            id="num-negative-int",
        ),
        pytest.param(
            "Z", asm.WhitespaceParamType.VALUE, get_expected_result("STSTTSTSL"), id="char"
        ),
        pytest.param(
            "00110101", asm.WhitespaceParamType.LABEL, get_expected_result("SSTTSTSTL"), id="label"
        ),
    ],
)
def test_translate_param(
    param: str | int, param_type: asm.WhitespaceParamType, expected_result: str
):
    result = asm.translate_param(param, param_type)

    assert result == expected_result


@pytest.mark.parametrize(
    "keyword,params,expected_instruction,expected_error",
    [
        pytest.param("junk", [], None, "Invalid instruction junk", id="invalid-keyword"),
    ]
    + [
        pytest.param(
            keyword,
            params,
            None,
            f"Expected 1 parameter for {keyword}, but got {len(params)}",
            id=f"{keyword}-{id_suffix}",
        )
        for keyword in ["push", "copy", "label", "call", "jump", "jumpz", "jumpn"]
        for params, id_suffix in [([], "too-few"), (["1", "'x'"], "too-many")]
    ]
    + [
        pytest.param(
            keyword,
            params,
            None,
            f"Expected no parameters for {keyword}, but got {len(params)}",
            id=f"{keyword}-too-many-{len(params)}",
        )
        for keyword in [
            "dup",
            "swap",
            "pop",
            "slide",
            "add",
            "sub",
            "div",
            "mod",
            "store",
            "retr",
            "ret",
            "end",
            "outc",
            "outn",
            "inc",
            "inn",
        ]
        for params in [["'a'"], ["'q'", "5"]]
    ]
    + [
        pytest.param("", [], "", "", id="comment"),
        pytest.param("dup", [], "SLS", "", id="dup"),
        pytest.param("swap", [], "SLT", "", id="swap"),
        pytest.param("pop", [], "SLL", "", id="pop"),
        pytest.param("slide", [], "STL", "", id="slide"),
        pytest.param("add", [], "TSSS", "", id="add"),
        pytest.param("sub", [], "TSST", "", id="sub"),
        pytest.param("mult", [], "TSSL", "", id="mult"),
        pytest.param("div", [], "TSTS", "", id="div"),
        pytest.param("mod", [], "TSTT", "", id="mod"),
        pytest.param("store", [], "TTS", "", id="store"),
        pytest.param("retr", [], "TTT", "", id="retr"),
        pytest.param("ret", [], "LTL", "", id="ret"),
        pytest.param("end", [], "LLL", "", id="end"),
        pytest.param("outc", [], "TLSS", "", id="outc"),
        pytest.param("outn", [], "TLST", "", id="outn"),
        pytest.param("inc", [], "TLTS", "", id="inc"),
        pytest.param("inn", [], "TLTT", "", id="inn"),
        pytest.param("push", ["33"], "SSSTSSSSTL", "", id="push-pos-num"),
        pytest.param("push", ["-25"], "SSTTTSSTL", "", id="push-neg-num"),
        pytest.param("push", ["'X'"], "SSSTSTTSSSL", "", id="push-char"),
        pytest.param(
            "push",
            ["x"],
            None,
            "Expected number or single character, but got x instead",
            id="push-invalid",
        ),
        pytest.param("copy", ["8"], "STSSTSSSL", "", id="copy-pos-num"),
        pytest.param("copy", ["-7"], "STSTTTTL", "", id="copy-neg-num"),
        pytest.param(
            "copy", ["'X'"], None, "Expected number, but got 'X' instead", id="copy-invalid"
        ),
        pytest.param("label", ["0101"], "LSSSTSTL", "", id="label-valid"),
        pytest.param(
            "label",
            ["'a'"],
            None,
            "Expected zeros and ones, but got 'a' instead",
            id="label-invalid",
        ),
        pytest.param("call", ["11000"], "LSTTTSSSL", "", id="call-valid"),
        pytest.param(
            "call", ["2"], None, "Expected zeros and ones, but got 2 instead", id="call-invalid"
        ),
        pytest.param("jump", ["0110"], "LSLSTTSL", "", id="jump-valid"),
        pytest.param(
            "jump", ["X"], None, "Expected zeros and ones, but got X instead", id="jump-invalid"
        ),
        pytest.param("jumpz", ["1010"], "LTSTSTSL", "", id="jumpz-valid"),
        pytest.param(
            "jumpz",
            ["123"],
            None,
            "Expected zeros and ones, but got 123 instead",
            id="jumpz-invalid",
        ),
        pytest.param("jumpn", ["000111"], "LTTSSSTTTL", "", id="jumpn-valid"),
        pytest.param(
            "jumpn", ["5"], None, "Expected zeros and ones, but got 5 instead", id="jumpn-invalid"
        ),
    ],
)
def test_translate_instruction(
    keyword: str, params: list[str], expected_instruction: str | None, expected_error: str
):
    instruction, error = asm.translate_instruction(keyword, params)

    expected_instruction = (
        get_expected_result(expected_instruction) if expected_instruction is not None else None
    )
    assert instruction == expected_instruction
    assert error == expected_error

    instruction, error = asm.translate_instruction(keyword.upper(), params)

    assert instruction == expected_instruction
    assert error == expected_error


@pytest.mark.parametrize(
    "format_type,instruction,expected_output",
    [
        pytest.param("raw", "STSTL", get_expected_result("STSTL"), id="raw"),
        pytest.param(
            "mark",
            "TTSLTS",
            f"T{asm.TAB}T{asm.TAB}S{asm.SPACE}L{asm.LF}T{asm.TAB}S{asm.SPACE}",
            id="mark",
        ),
    ],
)
def test_format_instruction(format_type: str, instruction: str, expected_output: str):
    instruction = get_expected_result(instruction)
    output = asm.format_instruction(format_type, instruction)

    assert output == expected_output


def get_example_params() -> list:
    params = []
    for dir_path in Path("examples").iterdir():
        if dir_path.name == "bad":
            continue

        base_path = dir_path / dir_path.name
        params += [
            pytest.param(
                Path(f"{base_path}.wsasm"),
                format_type,
                Path(f"{base_path}{ext}"),
                id=f"{dir_path.name}-{format_type}",
            )
            for format_type, ext in [("raw", ".ws.raw"), ("mark", ".ws")]
        ]

    return params


@pytest.mark.parametrize("input_path,format_type,expected_output_path", get_example_params())
def test_assemble(input_path: Path, format_type: str, expected_output_path: Path):
    input_contents = input_path.read_text(encoding="utf-8")
    output_contents, errors = asm.assemble(input_contents, format_type)

    expected_output_contents = expected_output_path.read_text(encoding="utf-8")
    assert output_contents == expected_output_contents
    assert not errors


def test_assemble_bad():
    input_contents = Path("examples/bad/bad.wsasm").read_text(encoding="utf-8")
    output_contents, errors = asm.assemble(input_contents, "raw")

    assert not output_contents

    expected_errors = [
        "Line 2: Invalid instruction junk",
        "Line 4: Expected 1 parameter for push, but got 0",
        "Line 5: Expected number, but got 'H' instead",
        "Line 6: Expected zeros and ones, but got 123 instead",
        "Line 8: Expected no parameters for pop, but got 1",
        "Line 9: Expected 1 parameter for push, but got 2",
    ]
    assert errors == expected_errors


@pytest.fixture()
def mock_assemble():
    with patch("whitespace_asm.asm.assemble") as mock:
        yield mock
