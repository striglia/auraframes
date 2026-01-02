import json
import os
from collections.abc import Sequence

from pydantic import BaseModel
from pydantic.json import pydantic_encoder


def build_path(*args: str, make_dir: bool = True) -> str:
    path = os.path.join(*args)
    if make_dir:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def write_model(model: BaseModel | Sequence[BaseModel], path: str) -> None:
    with open(path, "w") as out:
        json.dump(model, out, default=pydantic_encoder)
