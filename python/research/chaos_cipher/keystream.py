
"""Deterministic byte keystream generation from the fixed-point Lorenz system."""

from chaos_cipher.fixed_point import from_float, wrap_signed
from chaos_cipher.lorenz import rk2_step


def generate_keystream(
    length: int,
    x0: float = 1.0,
    y0: float = 1.0,
    z0: float = 1.0,
    warmup: int = 100,
) -> bytes:
    """Generate deterministic bytes from a Lorenz trajectory.

    This is a research baseline, not a cryptographically secure generator.
    """
    if length < 0:
        raise ValueError("length must be non-negative")
    if warmup < 0:
        raise ValueError("warmup must be non-negative")

    x = from_float(x0)
    y = from_float(y0)
    z = from_float(z0)

    # Discard initial transient states.
    for _ in range(warmup):
        x, y, z = rk2_step(x, y, z)

    output = bytearray()

    for _ in range(length):
        x, y, z = rk2_step(x, y, z)

        # Extract eight bits from the fractional portion of x.
        # Masking ensures the result is always in the range 0..255.
        byte_value = (wrap_signed(x) >> 8) & 0xFF
        output.append(byte_value)

    return bytes(output)
