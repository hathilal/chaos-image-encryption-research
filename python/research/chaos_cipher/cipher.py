
"""Baseline reversible byte cipher using the Lorenz keystream.

Research prototype only; not suitable for protecting real images.
"""

from chaos_cipher.keystream import generate_keystream


def encrypt(data: bytes, x0: float = 1.0, y0: float = 1.0,
            z0: float = 1.0, warmup: int = 100) -> bytes:
    """Encrypt bytes by XORing them with a deterministic keystream."""
    stream = generate_keystream(
        len(data), x0=x0, y0=y0, z0=z0, warmup=warmup
    )
    return bytes(value ^ key for value, key in zip(data, stream))


def decrypt(data: bytes, x0: float = 1.0, y0: float = 1.0,
            z0: float = 1.0, warmup: int = 100) -> bytes:
    """Decrypt using the same XOR keystream."""
    return encrypt(data, x0=x0, y0=y0, z0=z0, warmup=warmup)
