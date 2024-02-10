from collections.abc import Iterable
from typing import Any, Callable,TypeVar
from .values import Vec2

_T = TypeVar("_T")

def flatten_iterable(iterable: Iterable[Iterable[_T]]) -> list[_T]:
    return [x for y in iterable for x in y]

def reorder_dict(dict: dict, keys: (str)) -> dict:
    return {
        **{k: v for k, v in dict.items() if k in keys},
        **{k: v for k, v in dict.items() if k not in keys},
    }

def remove_where(l: list[_T], pred: Callable[[_T], bool]) -> list[_T]:
    i = 0
    r = []
    while i < len(l):
        if pred(l[i]):
            r.append(l[i])
            del l[i]
        else:
            i += 1

    return r

def calculate_arc(attrs: dict[str, Any]) -> tuple[Vec2, Vec2, Vec2]:
    start = attrs["start"]
    mid = attrs["mid"]
    end = attrs["end"]
    center = attrs["center"]
    radius = attrs["radius"]
    start_angle = attrs["start_angle"]
    end_angle = attrs["end_angle"]

    if (start is not None and mid is not None and end is not None and center is None and radius is None and start_angle is None and end_angle is None):
        return start, mid, end
    elif (start is None and mid is None and end is None and center is not None and radius is not None and start_angle is not None and end_angle is not None):
        c = Vec2(center)
        r = Vec2(radius, 0)
        return (
            c + r.rotate(start_angle),
            c + r.rotate((end_angle + start_angle) * 0.5),
            c + r.rotate(end_angle),
        )
    elif (start is not None and mid is None and end is None and center is not None and radius is None and start_angle is None and end_angle is not None):
        c = Vec2(center)
        r = start - center
        return (
            start,
            c + r.rotate(end_angle * 0.5),
            c + r.rotate(end_angle),
        )
    else:
        raise ValueError("Invalid initialization arguments for Arc. Specify either (start, mid, end) or (center, radius, start_angle, end_angle).")
