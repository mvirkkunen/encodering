from collections.abc import Iterable
from typing import Any

def flatten_list(iterable: Iterable[Iterable[Any]]) -> list[Any]:
    return [x for y in iterable for x in y]

def reorder_dict(dict: dict, keys: (str)) -> dict:
    return {
        **{k: v for k, v in dict.items() if k in keys},
        **{k: v for k, v in dict.items() if k not in keys},
    }

def remove_where(l: list, pred):
    i = 0
    r = []
    while i < len(l):
        if pred(l[i]):
            r.append(l[i])
            del l[i]
        else:
            i += 1

    return r
