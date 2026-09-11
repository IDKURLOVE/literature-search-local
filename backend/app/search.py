import re
from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class FieldCondition:
    field: str
    value: str


@dataclass
class BoolOp:
    op: str
    left: "Node"
    right: "Node"


@dataclass
class NearOp:
    distance: int
    left: "Node"
    right: "Node"


Node = Union[FieldCondition, BoolOp, NearOp]


FIELD_ALIASES = {
    "TI": "title",
    "AU": "author",
    "AB": "abstract",
    "SO": "venue",
    "PY": "year",
    "DO": "doi",
    "TS": "topic",
    "AF": "all",
    "IS": "issn",
}


class QueryParseError(Exception):
    pass


class WOSQueryParser:
    def __init__(self) -> None:
        self.tokens: List[str] = []
        self.pos = 0

    def tokenize(self, query: str) -> List[str]:
        pattern = re.compile(
            r'"[^"]*"|'
            r"\(|\)|"
            r"NEAR/\d+|"
            r"AND|OR|NOT|"
            r"[A-Z]{2}=|"
            r"[^\s()\"]+"
        )
        return pattern.findall(query)

    def parse(self, query: str) -> Node:
        self.tokens = self.tokenize(query.strip())
        self.pos = 0
        if not self.tokens:
            raise QueryParseError("Empty query")
        node = self.parse_expression()
        if self.pos < len(self.tokens):
            raise QueryParseError(f"Unexpected token: {self.tokens[self.pos]}")
        return node

    def current(self) -> Optional[str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self) -> Optional[str]:
        token = self.current()
        self.pos += 1
        return token

    def parse_expression(self) -> Node:
        node = self.parse_term()
        while True:
            token = self.current()
            if token is None:
                break
            upper = token.upper()
            if upper in {"OR", "AND", "NOT"}:
                self.consume()
                right = self.parse_term()
                node = BoolOp(upper, node, right)
            else:
                break
        return node

    def parse_term(self) -> Node:
        token = self.current()
        if token is None:
            raise QueryParseError("Unexpected end of query")

        if token == "(":
            self.consume()
            node = self.parse_expression()
            if self.current() != ")":
                raise QueryParseError("Missing closing parenthesis")
            self.consume()
            return node

        if len(token) >= 3 and token[:2].upper() in FIELD_ALIASES and token[2] == "=":
            field = token[:2].upper()
            self.consume()
            value_token = self.current()
            if value_token is None:
                raise QueryParseError(f"Missing value for field {field}=")
            self.consume()
            value = value_token.strip('"')
            left = FieldCondition(FIELD_ALIASES[field], value)

            next_token = self.current()
            if next_token and next_token.upper().startswith("NEAR/"):
                distance = int(next_token.split("/")[1])
                self.consume()
                right_value_token = self.current()
                if right_value_token is None:
                    raise QueryParseError("Missing right operand for NEAR/x")
                self.consume()
                right_value = right_value_token.strip('"')
                right = FieldCondition(FIELD_ALIASES[field], right_value)
                return NearOp(distance, left, right)

            return left

        self.consume()
        value = token.strip('"')
        return FieldCondition("all", value)
