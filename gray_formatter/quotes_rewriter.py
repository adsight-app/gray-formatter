#!/usr/bin/env python3
#
#  dynamic_quotes.py
r"""
Applies "dynamic quotes" to Python source code.
The rules are:
* Use double quotes ``"`` where possible.
* Use single quotes ``'`` for empty strings and single characters (``a``, ``\n`` etc.).
* Leave the quotes unchanged for multiline strings, f strings and raw strings.
"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import ast
import re
import sys
from typing import  Union, Tuple, List

import asttokens
from operator import itemgetter


class Rewriter(ast.NodeVisitor):
    """
    ABC for rewriting Python source files from an AST and a token stream.
    .. autosummary-widths:: 8/16
    """

    #: The original source.
    source: str

    #: The tokenized source.
    tokens: asttokens.ASTTokens

    replacements: List[Tuple[Tuple[int, int], str]]
    """
	The parts of code to replace.
	Each element comprises a tuple of ``(start char, end char)`` in :attr:`~.source`,
	and the new text to insert between these positions.
	"""

    def __init__(self, source: str):
        self.source = source
        self.tokens = asttokens.ASTTokens(source, parse=True)
        self.replacements: List[Tuple[Tuple[int, int], str]] = []

        assert self.tokens.tree is not None

    def rewrite(self) -> str:
        """
        Rewrite the source and return the new source.
        :returns: The reformatted source.
        """

        tree = self.tokens.tree
        assert tree is not None
        self.visit(tree)

        reformatted_source = self.source

        # Work from the bottom up
        for (start, end), replacement in sorted(
            self.replacements, key=itemgetter(0), reverse=True
        ):
            source_before = reformatted_source[:start]
            source_after = reformatted_source[end:]
            reformatted_source = "".join([source_before, replacement, source_after])

        return reformatted_source

    def record_replacement(self, text_range: Tuple[int, int], new_source: str) -> None:
        """
        Record a region of text to be replaced.
        :param text_range: The region of text to be replaced.
        :param new_source: The new text for that region.
        """

        self.replacements.append((text_range, new_source))


class QuoteRewriter(Rewriter):
    if sys.version_info[:2] < (3, 8):  # pragma: no cover (py38+)

        def visit_Str(self, node: ast.Str) -> None:
            self.rewrite_quotes_for_node(node)

    else:  # pragma: no cover (<py38)

        def visit_Constant(self, node: ast.Constant) -> None:
            if isinstance(node.value, str):
                self.rewrite_quotes_for_node(node)
            else:
                self.generic_visit(node)

    def visit_definition(
        self, node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> None:
        """
        Mark the docstring of the function or class to identify it later.
        :param node:
        """

        if node.body and isinstance(node.body[0], ast.Expr):
            doc_node = node.body[0].value
            doc_node.is_docstring = True  # type: ignore[attr-defined]

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.visit_definition(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.visit_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_definition(node)

    def rewrite_quotes_for_node(self, node: Union[ast.Str, ast.Constant]) -> None:
        """
        Mark the area for rewriting quotes in the given node.
        :param node:
        """

        text_range = self.tokens.get_text_range(node)

        if text_range == (0, 0):
            return

        string = self.source[text_range[0] : text_range[1]]

        if getattr(node, "is_docstring", False):
            # TODO: format docstring with triple quotes and correct indentation
            return
        else:
            if string in {'""', "''"}:
                self.record_replacement(text_range, "''")
            elif not re.match("^[\"']", string):
                return
            elif len(node.s) == 1:
                self.record_replacement(text_range, repr(node.s))
            elif "\n" in string:
                return
            elif "\n" in node.s or "\\n" in node.s:
                return
            else:
                self.record_replacement(
                    text_range,
                    repr(node.s)#.translate(_surrogate_translator),
                )