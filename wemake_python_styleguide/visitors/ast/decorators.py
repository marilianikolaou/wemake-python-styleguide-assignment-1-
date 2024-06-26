import ast

from typing_extensions import Final, final

from wemake_python_styleguide.logic.tree import attributes
from wemake_python_styleguide.types import AnyFunctionDef
from wemake_python_styleguide.violations.best_practices import (
    NewStyledDecoratorViolation,
)
from wemake_python_styleguide.visitors.base import BaseNodeVisitor
from wemake_python_styleguide.visitors.decorators import alias

_ALLOWED_DECORATOR_TYPES: Final = (
    ast.Attribute,
    ast.Call,
    ast.Name,
)


@final
@alias('visit_any_function', (
    'visit_FunctionDef',
    'visit_AsyncFunctionDef',
))
class WrongDecoratorVisitor(BaseNodeVisitor):
    """Checks decorators's correctness."""

    def visit_any_function(self, node: AnyFunctionDef) -> None:
        """Checks functions' decorators."""
        self._check_new_decorator_syntax(node)
        self.generic_visit(node)

    def _check_new_decorator_syntax(self, node: AnyFunctionDef) -> None:
        branch_coverage = [
            ("branch1", False), ("branch2", False), ("branch3", False)
        ]
        for decorator in node.decorator_list:
            branch_coverage[0] = ("branch1", True)
            if not self._is_allowed_decorator(decorator):
                branch_coverage[1] = ("branch2", True)
                self.add_violation(NewStyledDecoratorViolation(decorator))
            else:
                branch_coverage[2] = ("branch3", True)
            self._print_branch_coverage(branch_coverage)

    def _print_branch_coverage(self, branch_coverage):
        print()
        covered_branches = sum(hit for _, hit in branch_coverage)
        coverage_percentage = (covered_branches / len(branch_coverage)) * 100
        for branch, hit in branch_coverage:
            print(f"{branch} was {'hit' if hit else 'not hit'}")
        print(f"Branch Coverage: {coverage_percentage:.2f}%")

    def _is_allowed_decorator(self, node: ast.expr) -> bool:
        if not isinstance(node, _ALLOWED_DECORATOR_TYPES):
            return False

        if isinstance(node, ast.Name):
            return True  # Simple names are fine!

        return all(
            isinstance(part, _ALLOWED_DECORATOR_TYPES)
            for part in attributes.parts(node)
        )
