"""
PA 4: The USILang Symbol Table -- starter.

Complete Environment and check_program below. See
PA_04_The_USILang_Symbol_Table.md, Part B, for the full requirements.
"""

from typing import Optional

from parser import Assignment, BinOp, Declaration, Number, Program, Variable


class SemanticError(Exception):
    pass


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent = parent
        self._names: dict = {}

    def define(self, name: str, line: int) -> None:
        if name in self._names:
            original_line = self._names[name]
            raise SemanticError(
                f"Duplicate declaration of '{name}' "
                f"(line {line}; originally declared line {original_line})."
            )

        self._names[name] = line

    def resolve(self, name: str, line: Optional[int] = None) -> int:
        if name in self._names:
            return self._names[name]

        if self.parent is not None:
            return self.parent.resolve(name, line)

        if line is None:
            raise SemanticError(f"Use of undeclared variable '{name}'.")

        raise SemanticError(
            f"Use of undeclared variable '{name}' (line {line})."
        )


def check_program(ast: Program) -> Environment:
    env = Environment(parent=None)

    def check_expr(expr: object) -> None:
        if isinstance(expr, Number):
            return

        if isinstance(expr, Variable):
            env.resolve(expr.name, expr.line)
            return

        if isinstance(expr, BinOp):
            check_expr(expr.left)
            check_expr(expr.right)
            return

    for statement in ast.statements:
        if isinstance(statement, Declaration):
            check_expr(statement.expr)
            env.define(statement.name, statement.line)

        elif isinstance(statement, Assignment):
            env.resolve(statement.name, statement.line)
            check_expr(statement.expr)

    return env