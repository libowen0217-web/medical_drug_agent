from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any


def to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {field.name: to_dict(getattr(obj, field.name)) for field in fields(obj)}
    if isinstance(obj, dict):
        return {str(key): to_dict(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_dict(item) for item in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def to_json(obj: Any, ensure_ascii: bool = False, indent: int = 2) -> str:
    return json.dumps(to_dict(obj), ensure_ascii=ensure_ascii, indent=indent)

