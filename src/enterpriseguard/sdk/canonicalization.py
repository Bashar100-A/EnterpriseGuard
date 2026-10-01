"""RFC 8785 JSON Canonicalization Scheme helpers for ADIE contracts."""

from __future__ import annotations

from typing import Any

from jcs import canonicalize
from pydantic import BaseModel


def canonicalize_json(value: Any) -> bytes:
    """Serialize JSON-compatible primitives to RFC 8785 canonical UTF-8 bytes."""
    return canonicalize(value)


def canonicalize_model(model: BaseModel) -> bytes:
    """Canonicalize a Pydantic v2 model using its JSON-mode aliased fields."""
    primitives = model.model_dump(mode="json", by_alias=True)
    return canonicalize_json(primitives)