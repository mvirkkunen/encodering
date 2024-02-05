import math
import uuid

from dataclasses import dataclass
from enum import Enum
from typing import overload, Iterable, Self, TypeAlias

from . import sexpr

ToVec2: TypeAlias = "list[float] | (float, float) | () | Vec2 | Pos2"

@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    @overload
    def __init__(self): ...

    @overload
    def __init__(self, x: float, y: float): ...

    @overload
    def __init__(self, xy: ToVec2): ...

    def __init__(self, *args):
        if len(args) == 0 or (isinstance(args[0], Iterable) and len(args[0]) == 0):
            self.__init(0, 0)
        elif len(args) == 1:
            if isinstance(args[0], Iterable):
                self.__init(*args[0][:2])
            else:
                self.__init(args[0].x, args[0].y)
        elif len(args) == 2:
            self.__init(*args)
        else:
            raise ValueError(f"Invalid arguments for Vec2(): {args}")

    def __init(self, x: float, y: float):
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)

    def to_sexpr(self):
        return [self.x, self.y]

    @classmethod
    def from_sexpr(cls, e) -> Self:
        return Vec2(*e)

    def rotate(self, angle) -> Self:
        if angle == 0:
            return self

        s = math.sin(angle / 180 * math.pi)
        c = math.cos(angle / 180 * math.pi)

        return Vec2(
            c * self.x - s * self.y,
            s * self.x + c * self.y,
        )

    def __add__(self, other) -> Self:
        other = Vec2(other)
        return Vec2(self.x + other.x, self.y + other.y)

    def __mul__(self, other) -> Self:
        return Vec2(self.x * other, self.y * other)

ToPos2: TypeAlias = "Pos2 | ToVec2"

@dataclass(frozen=True)
class Pos2(Vec2):
    r: float

    @overload
    def __init__(self): ...

    @overload
    def __init__(self, x: float, y: float, r: float = 0): ...

    @overload
    def __init__(self, xy: ToVec2, r: float = 0): ...

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], Pos2):
            self.__init(args[0], args[0].r)
        elif len(args) == 1 and isinstance(args[0], Vec2):
            self.__init(args[0], 0)
        elif len(args) == 1 and isinstance(args[0], (tuple, list)):
            self.__init(args[0], args[0][2] if len(args[0]) >= 3 else kwargs.get("r", 0))
        elif len(args) == 2 and isinstance(args[0], (Vec2, tuple, list)):
            self.__init(args[0], args[1] if len(args) == 2 else kwargs.get("r", 0))
        elif len(args) == 0 or len(args) == 2:
            self.__init(args)
        elif len(args) == 3:
            self.__init(args[:2], args[2])
        else:
            raise ValueError(f"Invalid arguments for Pos2(): {args}")

    def __init(self, super_init: ToVec2 = (), r: float = 0):
        super().__init__(super_init)
        object.__setattr__(self, "r", r)

    def to_sexpr(self):
        return [self.x, self.y, self.r]

    @classmethod
    def from_sexpr(cls, e: sexpr.SExpr) -> Self:
        return Pos2(*e)

    def rotate(self, angle: float) -> Self:
        if angle == 0:
            return self

        return Pos2(Vec2(self).rotate(angle), self.r + angle)

    def set_rotation(self, r: float) -> Self:
        return Pos2(self.x, self.y, r)

    def flip_y(self) -> Self:
        return Pos2(self.x, -self.y, self.r)

    def __add__(self, other: Self) -> Self:
        other = Pos2(other).rotate(self.r)

        return Pos2(self.x + other.x, self.y + other.y, other.r)

@dataclass(frozen=True)
class Rgba:
    r: float
    g: float
    b: float
    a: float

    @overload
    def __init__(self): ...

    @overload
    def __init__(self, r: float, g: float, b: float, a: float): ...

    @overload
    def __init__(self, rgba: ToVec2): ...

    def __init__(self, *args):
        if len(args) == 0:
            self.__init(0, 0, 0, 0)
        elif len(args) == 1 and isinstance(args[0], Rgba):
            self.__init(args[0].r, args[0].g, args[0].b, args[0].a)
        elif len(args) == 1 and isinstance(args[0], (tuple, list)):
            self.__init(*args[0])
        elif len(args) == 4:
            self.__init(*args)
        else:
            raise ValueError("Invalid arguments for Rgba()")

    def __init(self, r: float, g: float, b: float, a: float):
        object.__setattr__(self, "r", r)
        object.__setattr__(self, "g", r)
        object.__setattr__(self, "b", r)
        object.__setattr__(self, "a", r)

    def to_sexpr(self):
        return [self.r, self.g, self.b, self.a]

    @classmethod
    def from_sexpr(cls, e) -> Self:
        return Rgba(*e)

class Uuid():
    __value: str

    def __init__(self, value: "str | Uuid" = None):
        if not value:
            self.__value = str(uuid.uuid4())
        elif isinstance(value, Uuid):
            self.__value = value.value
        else:
            self.__value = value

    @property
    def value(self):
        return self.__value

    def to_sexpr(self):
        return [sexpr.Sym(self.value)]

    @classmethod
    def from_sexpr(cls, e) -> Self:
        return Uuid(e[0].name)

class SymbolEnum(Enum):
    def to_sexpr(self):
        return [sexpr.Sym(self.value)]

    @classmethod
    def from_sexpr(cls, e) -> Self:
        for item in cls:
            if item.value == e[0].name:
                return item

        return SymbolEnumUnknownValue(e[0].name)

@dataclass(frozen=True)
class SymbolEnumUnknownValue:
    value: str

    def to_sexpr(self):
        return [sexpr.Sym(self.value)]

class Layer:
    FCu = "F.Cu"
    In1Cu = "In1.Cu"
    In2Cu = "In2.Cu"
    In3Cu = "In3.Cu"
    In4Cu = "In4.Cu"
    In5Cu = "In5.Cu"
    In6Cu = "In6.Cu"
    In7Cu = "In7.Cu"
    In8Cu = "In8.Cu"
    In9Cu = "In9.Cu"
    In10Cu = "In10.Cu"
    In11Cu = "In11.Cu"
    In12Cu = "In12.Cu"
    In13Cu = "In13.Cu"
    In14Cu = "In14.Cu"
    In15Cu = "In15.Cu"
    In16Cu = "In16.Cu"
    In17Cu = "In17.Cu"
    In18Cu = "In18.Cu"
    In19Cu = "In19.Cu"
    In20Cu = "In20.Cu"
    In21Cu = "In21.Cu"
    In22Cu = "In22.Cu"
    In23Cu = "In23.Cu"
    In24Cu = "In24.Cu"
    In25Cu = "In25.Cu"
    In26Cu = "In26.Cu"
    In27Cu = "In27.Cu"
    In28Cu = "In28.Cu"
    In29Cu = "In29.Cu"
    In30Cu = "In30.Cu"
    BCu = "B.Cu"
    BAdhes = "B.Adhes"
    FAdhes = "F.Adhes"
    BPaste = "B.Paste"
    FPaste = "F.Paste"
    BSilkS = "B.SilkS"
    FSilkS = "F.SilkS"
    BMask = "B.Mask"
    FMask = "F.Mask"
    DwgsUser = "Dwgs.User"
    CmtsUser = "Cmts.User"
    Eco1User = "Eco1.User"
    Eco2User = "Eco2.User"
    EdgeCuts = "Edge.Cuts"
    FCrtYd = "F.CrtYd"
    BCrtYd = "B.CrtYd"
    FFab = "F.Fab"
    BFab = "B.Fab"
    User1 = "User.1"
    User2 = "User.2"
    User3 = "User.3"
    User4 = "User.4"
    User5 = "User.5"
    User6 = "User.6"
    User7 = "User.7"
    User8 = "User.8"
    User9 = "User.9"
