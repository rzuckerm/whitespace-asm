[![Makefile CI](https://github.com/rzuckerm/whitespace-asm/actions/workflows/makefile.yml/badge.svg)](https://github.com/rzuckerm/whitespace-asm/actions/workflows/makefile.yml)
# whitespace-asm

Assembler for the [Whitespace](https://en.wikipedia.org/wiki/Whitespace_(programming_language))
Programming Language. It generates a Whitespace program based on a file containing a set of
keywords instead of having to type in whitespace characters.

See the [Whitespace Tutorial](https://web.archive.org/web/20150618184706/http://compsoc.dur.ac.uk/whitespace/tutorial.php)
for details on the Whitespace language.

## Keywords

Keywords are case-insensitive.

### Stack Manipulation

| Mnemonic | Parameter  | Description                                                                      |
| -------- | ---------- | -------------------------------------------------------------------------------- |
| `push`   | `<value>`  | Push the value onto the stack                                                    |
| `dup`    |            | Duplicate the top item on the stack                                              |
| `copy`   | `<number>` | Copy the nth item on the stack (given by the argument) onto the top of the stack |
| `swap`   |            | Swap the top two items on the stack                                              |
| `pop`    |            | Discard the top item on the stack                                                |
| `slide`  | `<number>` | Slide n items off the stack, keeping the top item                                |

### Arithmetic

| Mnemonic | Parameter  | Description                                                                      |
| -------- | ---------- | -------------------------------------------------------------------------------- |
| `add`    |            | Addition                                                                         |
| `sub`    |            | Subtraction                                                                      |
| `mult`   |            | Multiplication                                                                   |
| `div`    |            | Integer Division                                                                 |
| `mod`    |            | Modulo                                                                           |

### Heap Access

| Mnemonic | Parameter  | Description                                                                      |
| -------- | ---------- | -------------------------------------------------------------------------------- |
| `store`  |            | Store                                                                            |
| `retr`   |            | Retreive                                                                         |

### Flow Control

| Mnemonic | Parameter  | Description                                                                      |
| -------- | ---------- | -------------------------------------------------------------------------------- |
| `label`  | `<label>`  | Mark a location in the program                                                   |
| `call`   | `<label>`  | Call a subroutine                                                                |
| `jump`   | `<label>`  | Jump unconditionally to a label                                                  |
| `jumpz`  | `<label>`  | Jump to a label if the top of the stack is zero                                  |
| `jumpn`  | `<label>`  | Jump to a label if the top of the stack is negative                              |
| `ret`    |            | End a subroutine and transfer control back to the caller                         |
| `end`    |            | End the program                                                                  |

### I/O

| Mnemonic   | Parameter  | Description                                                                      |
| ---------- | ---------- | -------------------------------------------------------------------------------- |
| `outc`     |            | Output the character at the top of the stack                                     |
| `outn`     |            | Output the number at the top of the stack                                        |
| `inc`      |            | Read a character and place it in the location given by the top of the stack      |
| `inn`      |            | Read a number and place it in the location given by the top of the stack         |

### Comments

Comments may be on a separate line or may be inline. Comments start with `;`. Example:

```assembly
;This a comment
push 'H' ;Stack = 'H'
outc     ;Output 'H'
```

## Parameters

### `<number>`

`<number>` is just an integer value. It may be positive or negative. Examples:

- `42`
- `-33`

### `<value>`

`<value>` may either be a `<number>` or a character. A character is enclosed in single quotes.
Backslash may be used for characters like newline (`'\n'`). Examples of characters:

- `' '`
- `'H'`
- `';'`
- `'\n'` - Newline
- `'\''` - Single quote
- `'\\'` - Backslash

### `<label>`

`<label>` is a number that consists of just zeros and one. Examples:

- `011`
- `10101`

## CLI

### Assemble

Assemble a Whitespace program:

```
whitespace-asm <input> [-o/--output <output>] [-f/--format <format>]
```

where:

- `<input>` is the path to the input Whitespace Assembly file
- `<output>` is the optional path to output Whitespace file. If not specified,
  change the extension of `<input>` to `.ws`
- `<format>` is the optional output format type:
  - `raw`: just whitespace
  - `mark` (default): whitespace is preceeded by `S` (space), `T` (tab), and `L`
    (newline)

Example:

```
whitespace-asm hello-world.wsasm --output hello-world.ws
```
