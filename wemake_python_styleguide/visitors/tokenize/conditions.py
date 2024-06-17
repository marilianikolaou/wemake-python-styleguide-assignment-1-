import tokenize
from typing import ClassVar, FrozenSet, Sequence

from typing_extensions import final

from wemake_python_styleguide.violations.refactoring import (
    ImplicitElifViolation,
)
from wemake_python_styleguide.visitors.base import BaseTokenVisitor


@final
class IfElseVisitor(BaseTokenVisitor):
    """
    Checks if tokens tokens.

    We use ``tokenize`` instead of ``ast`` because

    .. code:: python

       if some:
           ...
        else:
            if other:
                ...

    has the same ``ast`` representation as:

    .. code:: python

      if some:
          ...
      elif other:
          ...

    That's why we have to use ``tokenize`` to find
    the raw tokens inside the text.

    """

    _idents: ClassVar[FrozenSet[int]] = frozenset((
        tokenize.INDENT,
        tokenize.DEDENT,
    ))

    _allowed_token_types: ClassVar[FrozenSet[int]] = frozenset((
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.COLON,
        tokenize.INDENT,
    ))

    def visit_name(self, token: tokenize.TokenInfo) -> None:
        """Checks that ``if`` nodes are defined correctly."""
        self._check_implicit_elif(token)

    def _check_implicit_elif(self, token: tokenize.TokenInfo) -> None:
        branch_coverage = [
            ("branch1", False), ("branch2", False), ("branch3", False), ("branch4", False)
        ]

        token_index = self.file_tokens.index(token)

        if self._is_invalid_token(token_index, token):
            branch_coverage[0] = ("branch1", True)
            self._print_branch_coverage(branch_coverage)
            return

        # There's a bug in coverage, I am not sure how to make it work.
        next_tokens = self.file_tokens[token_index + 1:]
        for index, next_token in enumerate(next_tokens):  # pragma: no cover
            branch_coverage[1] = ("branch2", True)
            if next_token.exact_type in self._allowed_token_types:
                branch_coverage[2] = ("branch3", True)
                continue
            elif next_token.string == 'if':
                branch_coverage[3] = ("branch4", True)
                self._check_complex_else(next_tokens, next_token, index)
            self._print_branch_coverage(branch_coverage)
            return

    def _does_else_belong_to_if(self, start_index: int) -> bool:
        branch_coverage = [
            ("branch1", False), ("branch2", False), ("branch3", False), ("branch4", False)
        ]

        previous_token = self.file_tokens[start_index - 1]

        if previous_token.type != tokenize.DEDENT:
            # This is not the first token on the line, which means that it can
            # also be "embedded" else: x if A else B
            branch_coverage[0] = ("branch1", True)
            self._print_branch_coverage(branch_coverage)
            return False

        for token in reversed(self.file_tokens[:start_index - 1]):
            branch_coverage[1] = ("branch2", True)
            if token.type != tokenize.NAME:
                branch_coverage[2] = ("branch3", True)
                continue

            # Here we rely upon an intuition that in Python else have to be
            # on the same level (same indentation) as parent statement.
            if token.start[1] == previous_token.start[1]:
                branch_coverage[3] = ("branch4", True)
                self._print_branch_coverage(branch_coverage)
                return token.string in {'if', 'elif'}
        self._print_branch_coverage(branch_coverage)
        return False

    def _if_has_code_below(
        self,
        remaining_tokens: Sequence[tokenize.TokenInfo],
    ) -> bool:
        """
        Checks code immediately below an if statement to remove false positives.

        Checks that, below an if that comes immediately after an else, there is
        more code to be considered so as not to throw an incorrect violation.
        """
        index = 1
        while remaining_tokens[index - 1].exact_type not in self._idents:
            index += 1

        if len(remaining_tokens) == index + 1:
            return False

        context_count = 1
        while context_count:
            next_token = remaining_tokens[index]
            if next_token.exact_type == tokenize.INDENT:
                context_count += 1
            if next_token.exact_type == tokenize.DEDENT:
                context_count -= 1
            index += 1

        return remaining_tokens[index].exact_type != tokenize.DEDENT

    def _check_complex_else(
        self,
        tokens: Sequence[tokenize.TokenInfo],
        current_token: tokenize.TokenInfo,
        index: int,
    ) -> None:
        complex_else = self._if_has_code_below(tokens[index + 1:])
        if not complex_else:
            self.add_violation(ImplicitElifViolation(current_token))

    def _is_invalid_token(self, index: int, token: tokenize.TokenInfo) -> bool:
        is_not_else = token.string != 'else'

        # `else` token can belong also to `for` and `try/except` statement,
        # which can trigger false positive for that violation.
        belongs_to_if = self._does_else_belong_to_if(index)
        return is_not_else or not belongs_to_if

    def _print_branch_coverage(self, branch_coverage):
        print()
        covered_branches = sum(hit for _, hit in branch_coverage)
        coverage_percentage = (covered_branches / len(branch_coverage)) * 100
        for branch, hit in branch_coverage:
            print(f"{branch} was {'hit' if hit else 'not hit'}")
        print(f"Branch Coverage: {coverage_percentage:.2f}%")
