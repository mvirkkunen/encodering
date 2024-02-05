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

    def __init(self, name: str) -> None:
        if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
            raise ValueError(f"Invalid symbol: '{name}'")

        object.__setattr__(self, "name", name)

    def __repr__(self) -> str:
        return f"Symbol({self.name})"

@dataclass(frozen=True)
class UnknownFlatSExpr:
    expr: "FlatSExpr"

FlatSExpr: TypeAlias = str | list[str] | UnknownFlatSExpr

@dataclass(frozen=True)
class UnknownSExpr:
    expr: "SExpr"

SExpr: TypeAlias = "str | float | int | sexpr.Sym | list[sexpr.SExpr] | sexpr.UnknownSExpr"

def to_sexpr(obj: Any) -> list[SExpr]:
    if isinstance(obj, (str, int, float, Sym)):
        return [obj]
    elif isinstance(obj, UnknownSExpr):
        return [UnknownSExpr(to_sexpr(obj.expr))]
    elif isinstance(obj, list):
        return [to_sexpr(item) for item in obj]
    elif hasattr(obj, "to_sexpr"):
        return obj.to_sexpr()
    else:
        raise ValueError(f"Cannot convert type {type(obj)} to SExpr")

def sexpr_length(expr: FlatSExpr) -> int:
    """Calculates length of flattened s-expr element."""
    if isinstance(expr, str):
        return len(expr)
    if isinstance(expr, UnknownFlatSExpr):
        return sexpr_length(expr.expr) + 1
    elif len(expr) == 0:
        return 2
    else:
        return sum(sexpr_length(child) for child in expr) + len(expr) - 1

def sexpr_collect(r: list[str], expr: FlatSExpr, indent: int, width: int) -> None:
    if isinstance(expr, str):
        r.append(expr)
    elif isinstance(expr, UnknownFlatSExpr):
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
    r: list[str] = []
    sexpr_collect(r, expr, 0, width)
    return "".join(r)

def sexpr_flatten(obj: Any, show_unknown: bool) -> list[FlatSExpr]:
    """Flattens an object to an s-expr tree with only lists and strings."""
    if isinstance(obj, Sym):
        return [obj.name]
    elif isinstance(obj, str):
        return [f"\"{repr(obj)[1:-1]}\""]
    elif isinstance(obj, int):
        return [str(obj)]
    elif isinstance(obj, float):
        return [str(round(obj * 1e6) / 1e6)]
    elif isinstance(obj, UnknownSExpr):
        if show_unknown:
            return [UnknownFlatSExpr(sexpr_flatten(obj.expr, show_unknown)[0])]
        else:
            return sexpr_flatten(obj.expr, show_unknown)
    elif isinstance(obj, list):
        return [flatten_list(sexpr_flatten(c, show_unknown) for c in obj)]
    else:
        raise ValueError(f"Cannot flatten type {type(obj)}")

def sexpr_serialize(obj: Any, width: int = 120, show_unknown: bool = False) -> str:
    return sexpr_format(sexpr_flatten(obj, show_unknown)[0], width)

numeric = "-0123456789."
symbol = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

def sexpr_parse(s: str) -> SExpr:
    root: list[SExpr] = []
    stack: list[list[SExpr]] = [root]

    i = 0
    while i < len(s):
        c = s[i]
        if c == "(":
            l: list[SExpr] = []
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
