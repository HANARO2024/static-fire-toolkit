# ruff: noqa: D103
from static_fire_toolkit.core import hello


def test_hello():
    assert "static-fire-toolkit" in hello()
