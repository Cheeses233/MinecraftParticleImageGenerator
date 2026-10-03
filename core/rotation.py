"""Euler rotation helpers shared by the model, renderer, and viewport."""

from __future__ import annotations

import math

Vector3 = tuple[float, float, float]
Rotation3 = tuple[float, float, float]


def rotate_vector(vector: Vector3, rotation_degrees: Rotation3) -> Vector3:
    """Rotate a vector around X, then Y, then Z in degrees."""
    x, y, z = vector
    rx, ry, rz = (math.radians(angle) for angle in rotation_degrees)

    cosine, sine = math.cos(rx), math.sin(rx)
    y, z = y * cosine - z * sine, y * sine + z * cosine

    cosine, sine = math.cos(ry), math.sin(ry)
    x, z = x * cosine + z * sine, -x * sine + z * cosine

    cosine, sine = math.cos(rz), math.sin(rz)
    x, y = x * cosine - y * sine, x * sine + y * cosine
    return x, y, z
