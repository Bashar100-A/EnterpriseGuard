"""Tests for deterministic RFC 8785 canonical serialization."""

import pytest
from pydantic import BaseModel, Field

from enterpriseguard.adie.canonicalization import canonicalize_json, canonicalize_model


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"b": 1, "a": 2}, b'{"a":2,"b":1}'),
        (
            {"numbers": [333333333.33333329, 1e30, 4.50, 2e-3]},
            b'{"numbers":[333333333.3333333,1e+30,4.5,0.002]}',
        ),
        (
            {"array": [3, {"z": False, "a": None}, "x"]},
            b'{"array":[3,{"a":null,"z":false},"x"]}',
        ),
        ({"text": "€"}, '{"text":"€"}'.encode("utf-8")),
        ({"negative_zero": -0.0}, b'{"negative_zero":0}'),
    ],
)
def test_canonicalize_json_known_vectors(value, expected):
    assert canonicalize_json(value) == expected


def test_canonicalize_json_is_deterministic_across_key_insertion_order():
    first = {"z": [1, 2], "a": {"y": True, "x": None}}
    second = {"a": {"x": None, "y": True}, "z": [1, 2]}

    assert canonicalize_json(first) == canonicalize_json(second)


def test_canonicalize_model_uses_json_mode_and_aliases():
    class ModelManifest(BaseModel):
        model_id: str = Field(alias="modelId")
        metadata: dict[str, int]

    manifest = ModelManifest(modelId="model-1", metadata={"z": 2, "a": 1})

    assert canonicalize_model(manifest) == b'{"metadata":{"a":1,"z":2},"modelId":"model-1"}'
    assert canonicalize_model(manifest) == canonicalize_model(manifest)