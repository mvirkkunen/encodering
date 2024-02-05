import hashlib
import gc
import os
import pickle
import re
import warnings
from typing import Any, Callable

def get_cache_path(path: str) -> str:
    cache_dir = os.environ.get("XDG_CACHE_HOME", None)
    if not cache_dir:
        cache_dir = os.environ.get("HOME", None)
        if cache_dir:
            cache_dir = os.path.join(cache_dir, ".cache")

    if not cache_dir:
        warnings.warn("You operating system does not seem to specify a cache directory in the standard way")
        return None

    cache_dir = os.path.join(cache_dir, "kigen")
    os.makedirs(cache_dir, mode=0o755, exist_ok=True)

    filename = (
        re.sub(r"[^a-zA-Z0-9_-]", "_", path)[:128]
        + "_"
        + hashlib.sha256(path.encode("utf-8")).hexdigest()
        + ".kigen_cache"
    )

    return os.path.join(cache_dir, filename)

def load(path: str, loader: Callable[[str], Any]) -> Any:
    mtime = os.path.getmtime(path)
    header = ("kigen_cache", 1, mtime)

    try:
        with open(get_cache_path(path), "rb") as f:
            p = pickle.Unpickler(f)
            if p.load() != header:
                raise FileNotFoundError()

            gc.disable()
            obj = p.load()

            return obj
    except (FileNotFoundError, PermissionError):
        pass
    finally:
        gc.enable()

    obj = loader(path)
    with open(get_cache_path(path), "wb") as f:
        p = pickle.Pickler(f)
        p.dump(header)
        p.dump(obj)

    return obj
