from __future__ import annotations

import ast
import functools
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from gray_formatter._ast_helpers import ast_to_offset
from gray_formatter._data import register
from gray_formatter._data import State
from gray_formatter._data import TokenFunc
from gray_formatter._token_helpers import find_call
from gray_formatter._token_helpers import fix_brace


def _fix_func(
        i: int,
        tokens: list[Token],
        *,
        arg_offsets: set[Offset],
) -> None:
    fix_brace(
        tokens,
        find_call(arg_offsets, i, tokens),
        add_comma=True,
        remove_comma=True,
    )


def visit_FunctionDef(
        state: State,
        node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> Iterable[tuple[Offset, TokenFunc]]:
    args = [*node.args.posonlyargs, *node.args.args]

    if node.args.vararg:
        args.append(node.args.vararg)
    if node.args.kwarg:
        args.append(node.args.kwarg)
    if node.args.kwonlyargs:
        args.extend(node.args.kwonlyargs)

    arg_offsets = {ast_to_offset(arg) for arg in args}

    if arg_offsets:
        func = functools.partial(_fix_func, arg_offsets=arg_offsets)
        yield ast_to_offset(node), func


register(ast.AsyncFunctionDef)(visit_FunctionDef)
register(ast.FunctionDef)(visit_FunctionDef)
