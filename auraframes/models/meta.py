from typing import Any, cast

import pydantic


class AllOptional(pydantic.main.ModelMetaclass):
    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespaces: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        annotations = namespaces.get("__annotations__", {})
        for base in bases:
            annotations.update(base.__annotations__)
        for field in annotations:
            if not field.startswith("__"):
                annotations[field] = annotations[field] | None
        namespaces["__annotations__"] = annotations
        return cast(type, super().__new__(cls, name, bases, namespaces, **kwargs))
