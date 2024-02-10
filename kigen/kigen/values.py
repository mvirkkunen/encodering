import math
import uuid

from dataclasses import dataclass
from enum import Enum
from typing import overload, Any, Optional, Tuple, TypeAlias

from . import sexpr

ToVec2: TypeAlias = "Vec2 | Pos2 | list[float] | Tuple[float, ...] | Tuple[()]"

@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, x: float, y: float, /) -> None: ...

    @overload
    def __init__(self, xy: ToVec2, /) -> None: ...

    def __init__(self, *args: Any) -> None:
        if not args:
            # Vec2()
            # Vec2(())
            self.__init(0, 0)
        elif len(args) == 1 and isinstance(args[0], (Vec2, Pos2)):
            # Vec2(vec2)
            # Vec2(pos2)
            self.__init(args[0].x, args[0].y)
        elif len(args) == 1 and isinstance(args[0], (list, tuple)):
            # Vec2((1, 2))
            # Vec2([1, 2])
            self.__init(*args[0][:2])
        elif len(args) == 2:
            # Vec2(1, 2)
            self.__init(*args)
        else:
            raise ValueError(f"Invalid initializer for Vec2(): {args}")

    def __init(self, x: float, y: float) -> None:
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)

    def to_sexpr(self) -> sexpr.SExpr:
        return [self.x, self.y]

    @classmethod
    def from_sexpr(cls, e: sexpr.SExpr) -> "Vec2":
        assert isinstance(e, list)

        return Vec2(*e)

    def rotate(self, angle: float) -> "Vec2":
        if angle == 0:
            return self

        s = math.sin(-angle / 180 * math.pi)
        c = math.cos(-angle / 180 * math.pi)

        return Vec2(
            c * self.x - s * self.y,
            s * self.x + c * self.y,
        )

    def length(self) -> float:
        return (self.x**2 + self.y**2)**0.5

    def __add__(self, other: "Vec2") -> "Vec2":
        other = Vec2(other)
        return Vec2(self.x + other.x, self.y + other.y)

ToPos2: TypeAlias = "ToVec2 | Tuple[float, ...]"

@dataclass(frozen=True)
class Pos2:
    x: float
    y: float
    r: float

    @overload
    def __init__(self) -> None:...

    @overload
    def __init__(self, x: float, y: float, r: float = 0, /) -> None: ...

    @overload
    def __init__(self, xy: ToVec2, r: float = 0, /) -> None: ...

    def __init__(self, *args: Any) -> None:
        if not args:
            # Pos2()
            # Pos2(())
            self.__init(0, 0, 0)
        elif len(args) == 1 and isinstance(args[0], Pos2):
            # Pos2(pos2)
            self.__init(args[0].x, args[0].y, args[0].r)
        elif len(args) == 1 and isinstance(args[0], Vec2):
            # Pos2(vec2)
            self.__init(args[0].x, args[0].y)
        elif len(args) == 1 and isinstance(args[0], (list, tuple)):
            # Pos2((1, 2, 3?))
            # Pos2([1, 2, 3?])
            self.__init(*args[0][:3])
        elif len(args) == 2 and isinstance(args[0], (list, tuple)):
            # Pos2((1, 2), 3)
            # Pos2([1, 2], 3)
            self.__init(args[0][0], args[0][1], args[1])
        elif len(args) == 2 and isinstance(args[0], (Pos2, Vec2)):
            # Pos2(pos2, 3)
            # Pos2(vec2, 3)
            self.__init(args[0].x, args[0].y, args[1])
        elif len(args) == 2 or len(args) == 3:
            # Pos2(1, 2, 3?)
            self.__init(*args[:3])
        else:
            raise ValueError(f"Invalid initializer for Vec2(): {args}")

    def __init(self, x: float, y: float, r: float = 0) -> None:
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "r", r)

    def to_sexpr(self) -> sexpr.SExpr:
        return [self.x, self.y, self.r]

    @classmethod
    def from_sexpr(cls, e: sexpr.SExpr) -> "Pos2":
        assert isinstance(e, list)

        return Pos2(*e)

    def rotate(self, angle: float) -> "Pos2":
        if angle == 0:
            return self

        return Pos2(Vec2(self).rotate(angle), self.r + angle)

    def set_rotation(self, r: float) -> "Pos2":
        return Pos2(self.x, self.y, r)

    def add_rotation(self, r: float) -> "Pos2":
        return Pos2(self.x, self.y, self.r + r)

    def flip_y(self) -> "Pos2":
        return Pos2(self.x, -self.y, self.r)

    def length(self) -> float:
        return (self.x**2 + self.y**2)**0.5

    def __add__(self, other: "ToPos2") -> "Pos2":
        v = Pos2(other).rotate(self.r)

        return Pos2(self.x + v.x, self.y + v.y, v.r)

    def __sub__(self, other: "ToPos2") -> "Pos2":
        return self + (-Pos2(other))

    def __neg__(self) -> "Pos2":
        return Pos2(-self.x, -self.y, -self.r)

@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def to_sexpr(self) -> sexpr.SExpr:
        return [self.x, self.y, self.z]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Vec3":
        assert isinstance(expr, list) and isinstance(expr[0], (float, int)) and isinstance(expr[1], (float, int)) and isinstance(expr[2], (float, int))

        return Vec3(expr[0], expr[1], expr[2])

@dataclass(frozen=True)
class Rgba:
    r: float
    g: float
    b: float
    a: float

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, r: float, g: float, b: float, a: float, /) -> None: ...

    @overload
    def __init__(self, rgba: "Rgba | tuple[float, float, float, float] | list[float]", /) -> None: ...

    def __init__(self, *args: Any) -> None:
        if not args:
            # Rgba()
            # Rgba(())
            self.__init(0, 0, 0, 0)
        elif len(args) == 1 and isinstance(args[0], Rgba):
            # Rgba(rgba)
            self.__init(args[0].r, args[0].g, args[0].b, args[0].a)
        elif len(args) == 1 and isinstance(args[0], (tuple, list)):
            # Rgba((1, 2, 3, 4))
            # Rgba([1, 2, 3, 4])
            self.__init(*args[0])
        elif len(args) == 4:
            # Rgba(1, 2, 3, 4)
            self.__init(*args)
        else:
            raise ValueError("Invalid arguments for Rgba()")

    def __init(self, r: float, g: float, b: float, a: float) -> None:
        object.__setattr__(self, "r", r)
        object.__setattr__(self, "g", g)
        object.__setattr__(self, "b", b)
        object.__setattr__(self, "a", a)

    def to_sexpr(self) -> sexpr.SExpr:
        return [self.r, self.g, self.b, self.a]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Rgba":
        assert isinstance(expr, list) and all(isinstance(e, float) or isinstance(e, int) for e in expr)

        return Rgba(*expr)

class Uuid():
    __value: str

    def __init__(self, value: "Optional[str | Uuid]" = None):
        if not value:
            self.__value = str(uuid.uuid4())
        elif isinstance(value, Uuid):
            self.__value = value.value
        else:
            self.__value = value

    @property
    def value(self) -> str:
        return self.__value

    def to_sexpr(self) -> sexpr.SExpr:
        return [sexpr.Sym(self.value)]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Uuid":
        assert isinstance(expr, list) and isinstance(expr[0], sexpr.Sym)

        return Uuid(expr[0].name)

    def __repr__(self) -> str:
        return repr(self.__value)

class SymbolEnum(Enum):
    def to_sexpr(self) -> sexpr.SExpr:
        return [sexpr.Sym(self.value)]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "SymbolEnum | SymbolEnumUnknownValue":
        assert isinstance(expr, list) and isinstance(expr[0], sexpr.Sym)

        for item in cls:
            if item.value == expr[0].name:
                return item

        return SymbolEnumUnknownValue(expr[0].name)

    def __repr__(self):
        return repr(self.value)

@dataclass(frozen=True)
class SymbolEnumUnknownValue:
    value: str

    def to_sexpr(self) -> sexpr.SExpr:
        return [sexpr.Sym(self.value)]
