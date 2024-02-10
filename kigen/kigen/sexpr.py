import itertools
import re

from dataclasses import dataclass
from typing import Protocol, Self, TypeAlias, TYPE_CHECKING

SYM_RE = r"[a-zA-Z0-9_*.-]+"
sym_re = re.compile("^" + SYM_RE + "$")
sym_name_to_id: dict[str, int] = {}
sym_id_to_name: dict[int, str] = {}

class Sym:
    __slots__ = ["sym_id"]

    sym_id: int

    def __init__(self, name: "str | Sym"):
        if isinstance(name, Sym):
            self.sym_id = name.sym_id
        else:
            sym_id = sym_name_to_id.get(name, None)
            if not sym_id:
                if not sym_re.match(name):
                    raise ValueError(f"Invalid symbol: '{name}'")

                sym_id = len(sym_name_to_id) + 1
                sym_name_to_id[name] = sym_id
                sym_id_to_name[sym_id] = name

            self.sym_id = sym_id

    @property
    def name(self) -> str:
        return sym_id_to_name[self.sym_id]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sym) and self.sym_id == other.sym_id

    def __repr__(self) -> str:
        return f"Symbol({self.name})"

    def __getnewargs__(self):
        return (self.name,)

@dataclass(frozen=True)
class UnknownFlatSExpr:
    expr: "FlatSExpr"

FlatSExpr: TypeAlias = str | list[str] | UnknownFlatSExpr

@dataclass(frozen=True)
class UnknownSExpr:
    expr: "SExpr"

SExprAtom: TypeAlias = str | int | float | Sym

# Absolutely no idea by Python and Mypy disagree on how this should be defined.
if TYPE_CHECKING:
    SExpr: TypeAlias = "SExprAtom | UnknownSExpr | list[SExpr]"
else:
    SExpr: TypeAlias = "sexpr.SExprAtom | sexpr.UnknownSExpr | list[sexpr.SExpr]"

class SExprConvert(Protocol):
    def to_sexpr(self) -> list[SExpr]: ...

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> Self: ...

def to_sexpr(obj: "SExpr | SExprConvert") -> list[SExpr]:
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

def sexpr_flatten(obj: SExpr, show_unknown: bool) -> list[FlatSExpr]:
    """Flattens an object to an s-expr tree with only lists and strings."""

    if isinstance(obj, Sym):
        return [obj.name]
    elif isinstance(obj, str):
        s = obj.encode("unicode_escape").decode("utf-8")
        return [f"\"{s}\""]
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
        return [list(itertools.chain.from_iterable(sexpr_flatten(e, show_unknown) for e in obj))] # type: ignore
    else:
        raise ValueError(f"Cannot flatten type {type(obj)}")

def sexpr_serialize(obj: SExpr, width: int = 120, show_unknown: bool = False) -> str:
    return sexpr_format(sexpr_flatten(obj, show_unknown)[0], width)

sexpr_re = re.compile(r"(\()|(\))|(-?[0-9]*\.[0-9]+(?=[ ()]))|(-?[0-9]+(?=[ ()]))|(" + SYM_RE + r")|\"((?:[^\\\"]*|\\.)*)\"|(\s+)", re.I)

def sexpr_parse(s: str) -> SExpr:
    root: list[SExpr] = []
    stack: list[list[SExpr]] = [root]

    i = 0
    while i < len(s):
        m = sexpr_re.match(s, i)
        if not m:
            raise ValueError(f"S-expression syntax error at offset {i}, near: {repr(s[i:i+32])}...")

        i = m.end(0)
        index = m.lastindex

        if index == 1:
            l: list[SExpr] = []
            stack[-1].append(l)
            stack.append(l)
        elif index == 2:
            stack.pop()
        elif index == 3:
            stack[-1].append(float(m.group(3)))
        elif index == 4:
            stack[-1].append(int(m.group(4)))
        elif index == 5:
            stack[-1].append(Sym(m.group(5)))
        elif index == 6:
            stack[-1].append(m.group(6).encode("utf-8").decode("unicode_escape"))

    return root[0]

