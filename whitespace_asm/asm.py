import argparse
import ast
import sys
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from pathlib import Path


# Whitespace parameter type
class WhitespaceParamType(IntFlag):
    NONE = 0x00
    NUMBER = 0x01
    CHAR = 0x02
    VALUE = NUMBER | CHAR
    MULTI_CHAR = 0x04
    LABEL = VALUE | MULTI_CHAR


# Whitespace command information
@dataclass
class WhitespaceInfo:
    command: str
    param_type: WhitespaceParamType = WhitespaceParamType.NONE


# Whitespace characters white character name abbreviation
SPACE = "S "
TAB = "T\t"
LF = "L\n"

# Whitespace command families
STACK = SPACE  # Stack Manipulation
MATH = TAB + SPACE  # Arithmetic
HEAP = TAB + TAB  # Heap Access
FLOW = LF  # Flow Control
IO = TAB + LF  # I/O

# Key is keyword, value is information about Whitespace command
TRANSLATION_TABLE: dict[str, WhitespaceInfo] = {
    # Stack Manipulation
    "push": WhitespaceInfo(command=STACK + SPACE, param_type=WhitespaceParamType.VALUE),
    "dup": WhitespaceInfo(command=STACK + LF + SPACE),
    "copy": WhitespaceInfo(command=STACK + TAB + SPACE, param_type=WhitespaceParamType.NUMBER),
    "swap": WhitespaceInfo(command=STACK + LF + TAB),
    "pop": WhitespaceInfo(command=STACK + LF + LF),
    "popn": WhitespaceInfo(command=STACK + TAB + LF),
    # Arithmetic
    "add": WhitespaceInfo(command=MATH + SPACE + SPACE),
    "sub": WhitespaceInfo(command=MATH + SPACE + TAB),
    "mult": WhitespaceInfo(command=MATH + SPACE + LF),
    "div": WhitespaceInfo(command=MATH + TAB + SPACE),
    "mod": WhitespaceInfo(command=MATH + TAB + TAB),
    # Heap Access
    "stor": WhitespaceInfo(command=HEAP + SPACE),
    "retr": WhitespaceInfo(command=HEAP + TAB),
    # Flow Control
    "mark": WhitespaceInfo(command=FLOW + SPACE + SPACE),
    "call": WhitespaceInfo(command=FLOW + SPACE + TAB),
    "jump": WhitespaceInfo(command=FLOW + SPACE + LF, param_type=WhitespaceParamType.LABEL),
    "jeq": WhitespaceInfo(command=FLOW + TAB + SPACE, param_type=WhitespaceParamType.LABEL),
    "jlt": WhitespaceInfo(command=FLOW + TAB + TAB, param_type=WhitespaceParamType.LABEL),
    "ret": WhitespaceInfo(command=FLOW + TAB + LF),
    "end": WhitespaceInfo(command=FLOW + LF + LF),
}


def main(args: list | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="path to the input Whitespace Assembly file")
    parser.add_argument("-o", "--output", help="optional path to output Whitespace file")
    parsed_args = parser.parse_args(args)

    input_path = Path(parsed_args.input)
    input_contents = input_path.read_text(encoding="utf-8")

    output_contents, errors = assemble(input_contents)

    if parsed_args.output:
        output_path = Path(parsed_args.output)
    else:
        output_path = input_path.parent / (input_path.stem + ".ws")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)

        sys.exit(1)

    output_path.write_text(output_contents, encoding="utf-8")


def assemble(input_contents: str) -> tuple[str, list[str]]:
    output_contents = ""
    errors = []
    return output_contents, errors


@dataclass
class ParsedLine:
    keyword: str = ""
    param: str = ""
    comment: str = ""


class ParserState(IntEnum):
    KEYWORD = 0
    PARAM_START = 1
    PARAM_START_CHAR = 2
    PARAM_BACKSLASH = 3
    PARAM_END_CHAR = 4
    PARAM_REST = 5


class ParserError(Exception):
    pass


def parse_line(line: str) -> ParsedLine:
    parsed_line = ParsedLine()
    parser_state = ParserState.KEYWORD
    line = line.strip()
    for index, ch in enumerate(line):
        if parser_state == ParserState.KEYWORD:
            if ch == ";":
                parsed_line.comment = line[index:]
                break

            if ch in (" ", "\t"):
                parser_state = ParserState.PARAM_START
            else:
                parsed_line.keyword += ch
        elif parser_state == ParserState.PARAM_START:
            if ch == ";":
                parsed_line.comment = line[index:]
                break

            parsed_line.param += ch
            if ch == "'":
                parser_state = ParserState.PARAM_START_CHAR
            else:
                parser_state = ParserState.PARAM_REST
        elif parser_state == ParserState.PARAM_START_CHAR:
            parsed_line.param += ch
            if ch == "'":
                parsed_line.comment = line[index + 1 :]
                break

            if ch == "\\":
                parser_state = ParserState.PARAM_BACKSLASH
            else:
                parser_state = ParserState.PARAM_END_CHAR
        elif parser_state == ParserState.PARAM_BACKSLASH:
            parsed_line.param += ch
            parser_state = ParserState.PARAM_END_CHAR
        elif parser_state == ParserState.PARAM_END_CHAR:
            parsed_line.param += ch
            if ch == "'":
                parsed_line.comment = line[index + 1 :]
                break
        else:
            if ch in (";", " ", "\t"):
                parsed_line.comment = line[index:]
                break

            parsed_line.param += ch

    parsed_line.param = parsed_line.param.strip()
    parsed_line.comment = parsed_line.comment.strip()
    if parsed_line.comment and not parsed_line.comment.startswith(";"):
        parsed_line.comment = f";{parsed_line.comment}"

    return parsed_line


def parse_number(param: str) -> int | None:
    result: int | None = None
    try:
        result = int(param)
    except ValueError:
        pass

    return result


def parse_string(param: str) -> str | None:
    result: str | None = None
    try:
        value = ast.literal_eval(param)
        if isinstance(value, str):
            result = value
    except SyntaxError:
        pass

    return result


def parse_param(param: str, param_type: WhitespaceParamType) -> str | int:
    result: str | int | None = None
    if param_type & WhitespaceParamType.NUMBER:
        result = parse_number(param)
        if result is not None:
            return result

        if param_type == WhitespaceParamType.NUMBER:
            raise ParserError(f"Number expected, but {param}")

    if param_type in [WhitespaceParamType.VALUE, WhitespaceParamType.LABEL]:
        result = parse_string(param)
        return result


def format_comment(comment: str) -> str:
    comment = comment.replace("' '", "'<space>'").replace(" ", "_")
    if not comment.endswith("_"):
        comment += "_"

    return comment
