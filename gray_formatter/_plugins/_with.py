from __future__ import annotations

import ast
import sys
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from gray_formatter._ast_helpers import ast_to_offset
from gray_formatter._data import register
from gray_formatter._data import State
from gray_formatter._data import TokenFunc
from gray_formatter._token_helpers import find_simple
from gray_formatter._token_helpers import fix_brace


if sys.version_info >= (3, 9):  # pragma: >=3.9 cover
    def _fix_with(i: int, tokens: list[Token]) -> None:
        i += 1
        if tokens[i].name == 'UNIMPORTANT_WS':
            i += 1
        if tokens[i].src == '(':
            fix = find_simple(i, tokens)
            # only fix if outer parens are for the with items (next is ':')
            if fix is not None and tokens[fix.braces[-1] + 1].src == ':':
                fix_brace(tokens, fix, add_comma=True, remove_comma=True)

    @register(ast.With)
    def visit_With(
        state: State,
        node: ast.With,
    ) -> Iterable[tuple[Offset, TokenFunc]]:
        yield ast_to_offset(node), _fix_with
