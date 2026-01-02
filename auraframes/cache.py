import json
import os
from collections.abc import Callable
from typing import Any, TypeVar

CACHE_DIR = "cache/"

F = TypeVar("F", bound=Callable[..., Any])

# TODO: Silly caching, should probably rework.


def save_to_cache(file_name: str, data: Any) -> None:
    path = os.path.join(CACHE_DIR, file_name + ".json")
    with open(path, "w") as f:
        json.dump(data, f)


def cache(file_name: str, use_arg: bool = False) -> Callable[[F], F]:
    def decorator(function: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if use_arg:
                path = os.path.join(CACHE_DIR, file_name + "-" + args[1] + ".json")
            else:
                path = os.path.join(CACHE_DIR, file_name + ".json")
            if os.path.isfile(path):
                with open(path) as f:
                    ret = json.load(f)
            else:
                with open(path, "w") as f:
                    ret = function(*args, **kwargs)
                    json.dump(ret, f)
            return ret

        return wrapper  # type: ignore[return-value]

    return decorator


def async_cache(file_name: str) -> Callable[[F], F]:
    def decorator(function: F) -> F:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            path = os.path.join(CACHE_DIR, file_name + ".json")
            if os.path.isfile(path):
                with open(path) as f:
                    ret = json.load(f)
            else:
                with open(path, "w") as f:
                    ret = await function(*args, **kwargs)
                    json.dump(ret, f)
            return ret

        return wrapper  # type: ignore[return-value]

    return decorator
