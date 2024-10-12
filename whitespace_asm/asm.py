import argparse
import ast
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


# Whitespace parameter type
class WhitespaceParamType(Enum):
    NONE = 0
    NUMBER = 1
    VALUE = 2
    LABEL = 3


# Whitespace command information
@dataclass
class WhitespaceInfo:
    command: str
    param_type: WhitespaceParamType = WhitespaceParamType.NONE


# Whitespace characters white character name abbreviation
SPACE = " "
TAB = "\t"
LF = "\n"

# Whitespace command families
STACK = SPACE  # Stack Manipulation
MATH = f"{TAB}{SPACE}"  # Arithmetic
HEAP = f"{TAB}{TAB}"  # Heap Access
FLOW = LF  # Flow Control
IO = f"{TAB}{LF}"  # I/O

# Key is keyword, value is information about Whitespace command
TRANSLATION_TABLE: dict[str, WhitespaceInfo] = {
    # Comment
    "": WhitespaceInfo(command=""),
    # Stack Manipulation
    "push": WhitespaceInfo(command=f"{STACK}{SPACE}", param_type=WhitespaceParamType.VALUE),
    "dup": WhitespaceInfo(command=f"{STACK}{LF}{SPACE}"),
    "copy": WhitespaceInfo(command=f"{STACK}{TAB}{SPACE}", param_type=WhitespaceParamType.NUMBER),
    "swap": WhitespaceInfo(command=f"{STACK}{LF}{TAB}"),
    "pop": WhitespaceInfo(command=f"{STACK}{LF}{LF}"),
    "slide": WhitespaceInfo(command=f"{STACK}{TAB}{LF}"),
    # Arithmetic
    "add": WhitespaceInfo(command=f"{MATH}{SPACE}{SPACE}"),
    "sub": WhitespaceInfo(command=f"{MATH}{SPACE}{TAB}"),
    "mult": WhitespaceInfo(command=f"{MATH}{SPACE}{LF}"),
    "div": WhitespaceInfo(command=f"{MATH}{TAB}{SPACE}"),
    "mod": WhitespaceInfo(command=f"{MATH}{TAB}{TAB}"),
    # Heap Access
    "store": WhitespaceInfo(command=f"{HEAP}{SPACE}"),
    "retr": WhitespaceInfo(command=f"{HEAP}{TAB}"),
    # Flow Control
    "label": WhitespaceInfo(command=f"{FLOW}{SPACE}{SPACE}", param_type=WhitespaceParamType.LABEL),
    "call": WhitespaceInfo(command=f"{FLOW}{SPACE}{TAB}", param_type=WhitespaceParamType.LABEL),
    "jump": WhitespaceInfo(command=f"{FLOW}{SPACE}{LF}", param_type=WhitespaceParamType.LABEL),
    "jumpz": WhitespaceInfo(command=f"{FLOW}{TAB}{SPACE}", param_type=WhitespaceParamType.LABEL),
    "jumpn": WhitespaceInfo(command=f"{FLOW}{TAB}{TAB}", param_type=WhitespaceParamType.LABEL),
    "ret": WhitespaceInfo(command=f"{FLOW}{TAB}{LF}"),
    "end": WhitespaceInfo(command=f"{FLOW}{LF}{LF}"),
    # I/O
    "outc": WhitespaceInfo(command=f"{IO}{SPACE}{SPACE}"),
    "outn": WhitespaceInfo(command=f"{IO}{SPACE}{TAB}"),
    "inc": WhitespaceInfo(command=f"{IO}{TAB}{SPACE}"),
    "inn": WhitespaceInfo(command=f"{IO}{TAB}{TAB}"),
}


def main(args: list | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="path to the input Whitespace Assembly file")
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "optional path to output Whitespace file. If not specified, the input filename "
            "is used with a '.ws' extension"
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["raw", "mark"],
        default="mark",
        help=(
            "output format: 'raw' is just whitespace; 'mark' (default) whitespace is preceeded "
            "by S (space), T (tab), and L (newline)"
        ),
    )
    parsed_args = parser.parse_args(args)

    input_path = Path(parsed_args.input)
    input_contents = input_path.read_text(encoding="utf-8")

    output_contents, errors = assemble(input_contents, parsed_args.format)
    if parsed_args.output:
        output_path = Path(parsed_args.output)
    else:
        output_path = input_path.parent / (input_path.stem + ".ws")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)

        sys.exit(1)

    output_path.write_text(output_contents, encoding="utf-8")


def assemble(input_contents: str, format_type: str) -> tuple[str, list[str]]:
    output_contents = ""
    errors = []
    for line_num, line in enumerate(input_contents.splitlines(), start=1):
        tokens = tokenize_line(line)
        command = parse_tokens(tokens)
        instruction, error = translate_instruction(command.keyword, command.params)
        if instruction is None:
            errors.append(f"Line {line_num}: {error}")
        else:
            output_contents += format_instruction(format_type, instruction)

    if errors:
        output_contents = ""

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


def parse_value(param: str) -> int | str | None:
    result: int | str | None = parse_number(param)
    if result is None:
        result = parse_string(param)
        if result is not None and len(result) != 1:
            result = None

    return result


def parse_label(param: str) -> str | None:
    result: str | None = None
    if param and all(ch in "01" for ch in param):
        result = param

    return result


def parse_param(param: str, param_type: WhitespaceParamType) -> tuple[str | int | None, str]:
    result: str | int | None = None
    if param_type == WhitespaceParamType.NUMBER:
        expected_type = "number"
        result = parse_number(param)
    elif param_type == WhitespaceParamType.VALUE:
        expected_type = "number or single character"
        result = parse_value(param)
    else:
        expected_type = "zeros and ones"
        result = parse_label(param)

    error = ""
    if result is None:
        error = f"Expected {expected_type}, but got {param} instead"

    return result, error


def translate_number(param: int) -> str:
    sign = SPACE if param >= 0 else TAB
    return sign + bin(abs(param))[2:].replace("0", SPACE).replace("1", TAB) + LF


def translate_string(param: str) -> str:
    return translate_number(ord(param[0]))


def translate_label(param: str) -> str:
    return param.replace("0", SPACE).replace("1", TAB) + LF


def translate_param(param: int | str, param_type: WhitespaceParamType) -> str:
    if param_type == WhitespaceParamType.LABEL:
        return translate_label(param)  # type: ignore

    if isinstance(param, int):
        return translate_number(param)

    return translate_string(param)


def translate_instruction(keyword: str, params: list[str]) -> tuple[str | None, str]:
    instruction: str | None = None
    error = ""
    keyword_lower = keyword.lower()
    translation_info = TRANSLATION_TABLE.get(keyword_lower)
    num_params = len(params)
    if not translation_info:
        error = f"Invalid instruction {keyword_lower}"
    elif translation_info.param_type == WhitespaceParamType.NONE and num_params != 0:
        error = f"Expected no parameters for {keyword_lower}, but got {num_params}"
    elif translation_info.param_type != WhitespaceParamType.NONE and num_params != 1:
        error = f"Expected 1 parameter for {keyword_lower}, but got {num_params}"
    else:
        if num_params:
            value, error = parse_param(params[0], translation_info.param_type)
            if value is not None:
                instruction = translation_info.command + translate_param(
                    value, translation_info.param_type
                )
        else:
            instruction = translation_info.command

    return instruction, error


def format_instruction(format_type: str, instruction: str) -> str:
    output_contents = instruction
    if format_type == "mark":
        output_contents = (
            output_contents.replace(SPACE, f"S{SPACE}")
            .replace(TAB, f"T{TAB}")
            .replace(LF, f"L{LF}")
        )

    return output_contents
