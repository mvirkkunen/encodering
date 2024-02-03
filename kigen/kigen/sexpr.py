from typing import Any, TypeAlias
from .values import Symbol
from .util import flatten_list

FlatSExpr: TypeAlias = str | list[str]

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

__all__ = ["sexpr_serialize", "FlatSexpr"]
