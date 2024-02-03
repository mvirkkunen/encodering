import re

from dataclasses import dataclass
from typing import Any, TypeAlias

from .util import flatten_list

@dataclass(frozen=True)
class Symbol:
    name: str

    def __init__(self, name: "str | Symbol"):
        if isinstance(name, Symbol):
            self.__init(name.name)
        else:
            self.__init(name)

    def __init(self, name):
        if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
            raise ValueError(f"Invalid symbol: '{name}'")

        object.__setattr__(self, "name", name)

FlatSExpr: TypeAlias = str | list[str]

SExpr: TypeAlias = "str | float | int | Symbol | list[SExpr]"

def length(e: FlatSExpr):
    """Calculates length of flattened s-expr element."""
    if isinstance(e, str):
        return len(e)
    elif len(e) == 0:
        return 2
    else:
        return sum(length(child) for child in e) + len(e) - 1

def collect(r: list[str], expr: FlatSExpr, indent: int, width: int):
    if isinstance(expr, str):
        r.append(expr)
        return

    if len(expr) == 0 or length(expr) <= width:
        r.append("(")
        for i, child in enumerate(expr):
            if i > 0:
                r.append(" ")

            collect(r, child, 0, width)
        r.append(")")
    else:
        r.append("(")
        for i, child in enumerate(expr):
            if i > 0:
                r.append("\n")
                r.append(" " * (indent + 2))
            collect(r, child, indent + 2, max(0, width - 2))
        r.append("\n")
        r.append(" " * indent)
        r.append(")")

def sexpr_format(expr: FlatSExpr, width: int = 120) -> str:
    r = []
    collect(r, expr, 0, width)
    return "".join(r)

def sexpr_serialize(obj: Any, width: int = 120) -> str:
    def flatten(o):
        """Flattens an object to an s-expr tree with only lists and strings."""
        if hasattr(o, "to_sexpr"):
            return [flatten(c)[0] for c in o.to_sexpr()]
        elif isinstance(o, Symbol):
            return [o.name]
        elif isinstance(o, str):
            return [f"\"{repr(o)[1:-1]}\""]
        elif isinstance(o, int):
            return [str(o)]
        elif isinstance(o, float):
            return [str(round(o * 1e6) / 1e6)]
        else:
            return [flatten_list(flatten(c) for c in o)]

    return sexpr_format(flatten(obj)[0], width)

numeric = "-0123456789."
symbol = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

def sexpr_parse(s: str) -> SExpr:
    root = []
    stack = [root]

    i = 0
    while i < len(s):
        c = s[i]
        if c == "(":
            l = []
            stack[-1].append(l)
            stack.append(l)
            i += 1
        elif c == ")":
            stack.pop()
            i += 1
        elif c == "\"":
            i += 1
            ss = ""
            while s[i] != "\"":
                ss += s[i]
                i += 1

            stack[-1].append(ss)
            i += 1
        elif c in numeric:
            ss = ""
            while s[i] in numeric:
                ss += s[i]
                i += 1

            stack[-1].append(float(ss) if "." in ss else int(ss))
        elif c in symbol:
            ss = ""
            while s[i] in symbol:
                ss += s[i]
                i += 1

            stack[-1].append(Symbol(ss))
        else:
            i += 1

    return root[0]

__all__ = ["sexpr_serialize", "FlatSexpr"]
