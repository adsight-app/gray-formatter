from __future__ import annotations

import ast
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from gray_formatter._ast_helpers import ast_to_offset
from gray_formatter._data import register
from gray_formatter._data import State
from gray_formatter._data import TokenFunc
from gray_formatter._token_helpers import find_simple
from gray_formatter._token_helpers import Fix
from gray_formatter._token_helpers import fix_brace


def _find_import(i: int, tokens: list[Token]) -> Fix | None:
    # progress forwards until we find either a `(` or a newline
    for i in range(i, len(tokens)):
        token = tokens[i]
        if token.name == 'NEWLINE':
            return None
        elif token.name == 'OP' and token.src == '(':
            return find_simple(i, tokens)
    else:
        raise AssertionError('Past end?')


def _fix_import(i: int, tokens: list[Token]) -> None:
    fix_brace(
        tokens,
        _find_import(i, tokens),
        add_comma=True,
        remove_comma=True,
    )


@register(ast.ImportFrom)
def visit_ImportFrom(
        state: State,
        node: ast.ImportFrom,
) -> Iterable[tuple[Offset, TokenFunc]]:
    yield ast_to_offset(node), _fix_import
