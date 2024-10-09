import argparse
import ast
import sys
from dataclasses import dataclass, field
from enum import IntFlag
from pathlib import Path
from typing import Callable


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
class TokenizerState:
    line: str
    idx: int = 0

    def curr(self) -> str:
        ch = self.get_char()
        self.unget_char(ch)
        return ch

    def next(self) -> str:
        ch = ""
        if self.idx < len(self.line):
            ch = self.line[self.idx]
            self.idx += 1

        return ch

    def get_char(self) -> str:
        ch = self.next()
        if ch == "\\":
            ch += self.next()

        return ch

    def unget_char(self, ch: str):
        self.idx = max(0, self.idx - len(ch))

    def take_while(self, pred: Callable[[str], bool]) -> str:
        token = ""
        while (ch := self.get_char()) and pred(ch):
            token += ch

        self.unget_char(ch)
        return token

    def take_until(self, pred: Callable[[str], bool]) -> str:
        token = ""
        while ch := self.get_char():
            token += ch
            if pred(ch):
                break

        return token


def tokenize_line(line: str) -> list[str]:
    state = TokenizerState(line)
    tokens = []
    while token := get_next_token(state):
        tokens.append(token)

    return tokens


def get_next_token(state: TokenizerState) -> str:
    token = ""
    state.take_while(lambda ch: ch in " \t")
    if state.curr() == ";":
        token += state.take_while(lambda _: True)

    while (ch := state.curr()) and ch not in " ;\t":
        if ch == "'":
            token += state.get_char() + state.take_until(lambda ch: ch == "'")
        else:
            token += state.take_while(lambda ch: ch not in " \t';")

    return token.strip()


@dataclass
class ParsedCommand:
    keyword: str = ""
    params: list[str] = field(default_factory=list)
    comment: str = ""


def parse_tokens(tokens: list[str]) -> ParsedCommand:
    command = ParsedCommand()
    if tokens and tokens[-1].startswith(";"):
        command.comment = tokens.pop()

    if tokens:
        command.keyword = tokens[0]
        command.params = tokens[1:]

    return command


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
    except (ValueError, SyntaxError):
        pass

    return result


def parse_param(param: str, param_type: WhitespaceParamType) -> tuple[str | int | None, str]:
    result: str | int | None = None
    if param_type == WhitespaceParamType.NUMBER:
        expected_type = "number"
    elif param_type == WhitespaceParamType.VALUE:
        expected_type = "number or single character"
    else:
        expected_type = "number, single character, or multiple characters"

    result = parse_number(param)
    if result is None and param_type in [WhitespaceParamType.VALUE, WhitespaceParamType.LABEL]:
        result = parse_string(param)
        if result is not None and (
            not result or (param_type == WhitespaceParamType.VALUE and len(result) != 1)
        ):
            result = None

    error = ""
    if result is None:
        error = f"Expected {expected_type}, but got {param} instead"

    return result, error


def translate_number(param: int) -> str:
    sign = SPACE if param >= 0 else TAB
    return sign + bin(abs(param))[2:].replace("0", SPACE).replace("1", TAB) + LF


def translate_string(param: str) -> str:
    value = 0
    for ch in param:
        value = value * 256 + ord(ch)

    return translate_number(value)


def translate_param(param: int | str) -> str:
    if isinstance(param, int):
        return translate_number(param)

    return translate_string(param)


def translate_instruction(keyword: str, params: list[str]) -> tuple[str | None, str]:
    instruction: str | None = None
    error = ""
    translation_info = TRANSLATION_TABLE.get(keyword.lower())
    num_params = len(params)
    if not translation_info:
        error = f"{keyword} is not a valid instruction"
    elif translation_info.param_type == WhitespaceParamType.NONE and num_params != 0:
        error = f"Expected no parameters, but got {num_params}"
    elif translation_info.param_type != WhitespaceParamType.NONE and num_params != 1:
        error = f"Expected 1 parameter, but got {num_params}"
    else:
        instruction = translation_info.command
        if num_params:
            value, error = parse_param(params[0], translation_info.param_type)
            if not error:
                instruction += translate_param(value)

    return instruction, error


def format_comment(comment: str) -> str:
    comment = comment.replace("' '", "'<space>'").replace(" ", "_")
    if not comment.endswith("_"):
        comment += "_"

    return comment
