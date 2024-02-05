import re

from dataclasses import dataclass
from typing import Any, TypeAlias

from .util import flatten_list

@dataclass(frozen=True)
class Sym:
    name: str

    def __init__(self, name: "str | Sym"):
        if isinstance(name, Sym):
            self.__init(name.name)
        else:
            self.__init(name)

    def __init(self, name):
        if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
            raise ValueError(f"Invalid symbol: '{name}'")

        object.__setattr__(self, "name", name)

@dataclass(frozen=True)
class UnknownSExpr:
    expr: "SExpr"

FlatSExpr: TypeAlias = str | list[str]

SExpr: TypeAlias = "str | float | int | Sym | list[SExpr]"

def sexpr_length(expr: FlatSExpr):
    """Calculates length of flattened s-expr element."""
    if isinstance(expr, str):
        return len(expr)
    if isinstance(expr, UnknownSExpr):
        return sexpr_length(expr.expr) + 1
    elif len(expr) == 0:
        return 2
    else:
        return sum(sexpr_length(child) for child in expr) + len(expr) - 1

def sexpr_collect(r: list[str], expr: FlatSExpr, indent: int, width: int):
    if isinstance(expr, str):
        r.append(expr)
    elif isinstance(expr, UnknownSExpr):
        r.append("?")
        sexpr_collect(r, expr.expr, indent, max(0, width - 1))
    elif len(expr) == 0 or sexpr_length(expr) <= width:
        r.append("(")
        for i, child in enumerate(expr):
            if i > 0:
                r.append(" ")

            sexpr_collect(r, child, 0, width)
        r.append(")")
    else:
        r.append("(")
        for i, child in enumerate(expr):
            if i > 0:
                r.append("\n")
                r.append(" " * (indent + 2))
            sexpr_collect(r, child, indent + 2, max(0, width - 2))
        r.append("\n")
        r.append(" " * indent)
        r.append(")")

def sexpr_format(expr: FlatSExpr, width: int = 120) -> str:
    r = []
    sexpr_collect(r, expr, 0, width)
    return "".join(r)

def sexpr_flatten(o, show_unknown: bool):
    """Flattens an object to an s-expr tree with only lists and strings."""
    if hasattr(o, "to_sexpr"):
        return [sexpr_flatten(c, show_unknown)[0] for c in o.to_sexpr()]
    elif isinstance(o, Sym):
        return [o.name]
    elif isinstance(o, str):
        return [f"\"{repr(o)[1:-1]}\""]
    elif isinstance(o, int):
        return [str(o)]
    elif isinstance(o, float):
        return [str(round(o * 1e6) / 1e6)]
    elif isinstance(o, UnknownSExpr):
        if show_unknown:
            return [UnknownSExpr(sexpr_flatten(o.expr, show_unknown)[0])]
        else:
            return sexpr_flatten(o.expr, show_unknown)
    else:
        return [flatten_list(sexpr_flatten(c, show_unknown) for c in o)]

def sexpr_serialize(obj: Any, width: int = 120, show_unknown: bool = False) -> str:
    return sexpr_format(sexpr_flatten(obj, show_unknown)[0], width)

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

            stack[-1].append(Sym(ss))
        else:
            i += 1

    return root[0]

__all__ = ["sexpr_serialize", "FlatSexpr"]
