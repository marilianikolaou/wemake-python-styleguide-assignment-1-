"""
Calculates cognitive complexity metric for nodes and functions.

Because Cyclomatic Complexity doesn't measure maintainability.
We need a metric to show how easily can a piece of code be understood.

Basic criteria. We boiled that guiding principle down into three simple rules:

- Increment when there is a break in the linear
  (top-to-bottom, left-to-right) flow of the code
- Increment when structures that break the flow are nested
- Ignore "shorthand" structures that readably condense
  multiple lines of code into one

Adapted from https://github.com/Melevir/cognitive_complexity
"""

import ast
from typing import Callable, Tuple

from wemake_python_styleguide.logic.tree import bools, recursion
from wemake_python_styleguide.types import AnyFunctionDef, AnyNodes

#: Control flow nodes that increment and can be nested.
_CONTROL_FLOW_BREAKERS: AnyNodes = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.IfExp,
)

#: Control flow nodes that increment.
_SHORT_CIRCUITS: AnyNodes = (
    ast.Break,
    ast.Continue,
    ast.Raise,
)

#: Basic nodes to be counted as `1`.
_INCREMENTERS: AnyNodes = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
)


def _process_child_nodes(
    node: ast.AST,
    increment_by: int,
    complexity_calculator: Callable[[ast.AST, int], int],
) -> int:
    branch_coverage = [("function1_branch1", False),("function1_branch2", False),("function1_branch3", False),("function1_branch4", False),("function1_branch5", False)]
    child_complexity = 0

    for node_num, child_node in enumerate(ast.iter_child_nodes(node)):
        branch_coverage[0] = ("function1_branch1", True)
        if isinstance(node, ast.Try):
            if node_num == 1:
                branch_coverage[1] = ("function1_branch2", True)
                increment_by += 1  # add +1 for all try nodes except body
            else:
                branch_coverage[2] = ("function1_branch3", True)

            if node_num:
                child_complexity += max(1, increment_by)
                branch_coverage[3] = ("function1_branch4", True)
            else :
                branch_coverage[4] = ("function1_branch5", True)

        child_complexity += complexity_calculator(
            child_node,
            increment_by,
        )
    covered_branches = sum(hit for _, hit in branch_coverage)
    coverage_percentage = (covered_branches /5) * 100
    print()
    for i ,(branch, hit) in enumerate(branch_coverage):
        print(f"{branch} was {'hit' if hit else 'not hit'}")
        i+=1
    print(f"Branch Coverage: {coverage_percentage:}%")
    return child_complexity


def _process_node_itself(
    node: ast.AST,
    increment_by: int,
) -> Tuple[int, int, bool]:
    if isinstance(node, _SHORT_CIRCUITS):
        return increment_by, max(1, increment_by), True
    elif isinstance(node, _CONTROL_FLOW_BREAKERS):
        increment_by += 1
        return increment_by, max(1, increment_by), True
    elif isinstance(node, _INCREMENTERS):
        increment_by += 1
        return increment_by, 0, True
    elif isinstance(node, ast.BoolOp):
        inner_boolops_amount = bools.count_boolops(node)
        base_complexity = inner_boolops_amount * max(increment_by, 1)
        return increment_by, base_complexity, False
    return increment_by, 0, True


def _get_cognitive_complexity_for_node(
    node: ast.AST,
    increment_by: int = 0,
) -> int:
    increment_by, base_complexity, should_iter_children = _process_node_itself(
        node,
        increment_by,
    )

    child_complexity = 0
    if should_iter_children:
        child_complexity += _process_child_nodes(
            node,
            increment_by,
            _get_cognitive_complexity_for_node,
        )

    return base_complexity + child_complexity


def cognitive_score(funcdef: AnyFunctionDef) -> int:
    """
    A thin wrapper around 3rd party dependency.

    We only need to be sure that our visitors API does not directly
    related to some 3rd party code.
    """
    complexity = sum(
        _get_cognitive_complexity_for_node(node)
        for node in funcdef.body
    )
    if recursion.has_recursive_calls(funcdef):
        complexity += 1
    return complexity
