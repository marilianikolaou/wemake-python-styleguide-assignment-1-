import ast

from typing_extensions import final

from wemake_python_styleguide.types import AnyFunctionDef
from wemake_python_styleguide.violations.consistency import (
    MultilineFunctionAnnotationViolation,
)
from wemake_python_styleguide.visitors.base import BaseNodeVisitor
from wemake_python_styleguide.visitors.decorators import alias


@final
@alias('visit_any_function', (
    'visit_FunctionDef',
    'visit_AsyncFunctionDef',
))
class WrongAnnotationVisitor(BaseNodeVisitor):
    """Ensures that annotations are used correctly."""

    def visit_any_function(self, node: AnyFunctionDef) -> None:
        """Checks return type annotations."""
        self._check_return_annotation(node)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Checks arguments annotations."""
        self._check_arg_annotation(node)
        self.generic_visit(node)

    def _check_return_annotation(self, node: AnyFunctionDef) -> None:
        branch_coverage = [
            ("branch1", False), ("branch2", False), ("branch3", False)
        ]

        if not node.returns:
            branch_coverage[0] = ("branch1", True)
            self._print_branch_coverage(branch_coverage)
            return

        for sub_node in ast.walk(node.returns):
            branch_coverage[1] = ("branch2", True)
            lineno = getattr(sub_node, 'lineno', None)
            if lineno and lineno != node.returns.lineno:
                branch_coverage[2] = ("branch3", True)
                self._print_branch_coverage(branch_coverage)
                self.add_violation(MultilineFunctionAnnotationViolation(node))
                return
        self._print_branch_coverage(branch_coverage)

    def _check_arg_annotation(self, node: ast.arg) -> None:
        branch_coverage = [
            ("branch1", False), ("branch2", False)
        ]

        for sub_node in ast.walk(node):
            branch_coverage[0] = ("branch1", True)
            lineno = getattr(sub_node, 'lineno', None)
            if lineno and lineno != node.lineno:
                branch_coverage[1] = ("branch2", True)
                self._print_branch_coverage(branch_coverage)
                self.add_violation(MultilineFunctionAnnotationViolation(node))
                return

        self._print_branch_coverage(branch_coverage)


    def _print_branch_coverage(self, branch_coverage):
        print()
        covered_branches = sum(hit for _, hit in branch_coverage)
        coverage_percentage = (covered_branches / len(branch_coverage)) * 100
        for branch, hit in branch_coverage:
            print(f"{branch} was {'hit' if hit else 'not hit'}")
        print(f"Branch Coverage: {coverage_percentage:.2f}%")


