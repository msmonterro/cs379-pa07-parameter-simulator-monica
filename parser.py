"""
USILang parser dependency: completed PA 3 interface.

Complete the parsing functions below. AST node types are already
defined -- do not modify them. See the assignment,
Part B, for the full requirements.
"""

from dataclasses import dataclass, field
from typing import List

from lexer import Token, tokenize


@dataclass
class Program:
    statements: list


@dataclass
class Declaration:
    name: str
    expr: object
    line: int


@dataclass
class Assignment:
    name: str
    expr: object
    line: int


@dataclass
class BinOp:
    op: str
    left: object
    right: object
    line: int


@dataclass
class Number:
    value: int
    line: int


@dataclass
class Variable:
    name: str
    line: int


class ParseError(Exception):
    pass


class _ParserState:
    """Given: a small cursor wrapper over the token list. Not required to use, but handy."""

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, type_: str) -> Token:
        tok = self.peek()
        if tok.type != type_:
            raise ParseError(f"Line {tok.line}: expected {type_}, found {tok.type} ({tok.lexeme!r}).")
        return self.advance()


def parse_factor(state: _ParserState):
    tok = state.peek()
    if tok.type == "NUMBER":
        state.advance()
        return Number(int(tok.lexeme), tok.line)
    if tok.type == "IDENT":
        state.advance()
        return Variable(tok.lexeme, tok.line)
    if tok.type == "LPAREN":
        state.advance()
        expr = parse_expr(state)
        state.expect("RPAREN")
        return expr
    raise ParseError(f"Line {tok.line}: expected a number, variable, or '(', found {tok.type}.")


def parse_term(state: _ParserState):
    expr = parse_factor(state)
    while state.peek().type in ("STAR", "SLASH"):
        op = state.advance()
        expr = BinOp(op.lexeme, expr, parse_factor(state), op.line)
    return expr


def parse_expr(state: _ParserState):
    expr = parse_term(state)
    while state.peek().type in ("PLUS", "MINUS"):
        op = state.advance()
        expr = BinOp(op.lexeme, expr, parse_term(state), op.line)
    return expr


def parse_declaration(state: _ParserState) -> Declaration:
    start = state.expect("LET")
    name = state.expect("IDENT")
    state.expect("ASSIGN")
    expr = parse_expr(state)
    state.expect("SEMI")
    return Declaration(name.lexeme, expr, start.line)


def parse_assignment(state: _ParserState) -> Assignment:
    name = state.expect("IDENT")
    state.expect("ASSIGN")
    expr = parse_expr(state)
    state.expect("SEMI")
    return Assignment(name.lexeme, expr, name.line)


def parse_statement(state: _ParserState):
    tok = state.peek()
    if tok.type == "LET":
        return parse_declaration(state)
    if tok.type == "IDENT":
        return parse_assignment(state)
    raise ParseError(f"Line {tok.line}: expected a declaration or assignment, found {tok.type}.")


def parse_program(state: _ParserState) -> Program:
    statements = []
    while state.peek().type != "EOF":
        statements.append(parse_statement(state))
    state.expect("EOF")
    return Program(statements)


def parse(tokens: List[Token]) -> Program:
    state = _ParserState(tokens)
    return parse_program(state)
