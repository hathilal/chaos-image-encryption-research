"""Experimental bidirectional diffusion cipher.

Research prototype. Not intended for production security.
"""

from chaos_cipher.permutation_diffusion import (
    _validate_data,
    _make_schedule,
)


def encrypt(data, x0=1.0, y0=1.0, z0=1.0, warmup=100, iv=0):
    plaintext = _validate_data(data)

    if not isinstance(iv, int) or not 0 <= iv <= 255:
        raise ValueError("iv must be an integer from 0 to 255")
    if not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a non-negative integer")

    n = len(plaintext)
    if n == 0:
        return b""

    permutation, stream = _make_schedule(
        n, x0, y0, z0, warmup
    )

    permuted = bytearray(n)
    for i, source_index in enumerate(permutation):
        permuted[i] = plaintext[source_index]

    # Forward diffusion.
    forward = bytearray(n)
    previous = iv
    for i in range(n):
        forward[i] = (permuted[i] + stream[i] + previous) & 0xFF
        previous = forward[i]

    # Reverse diffusion: use a separate deterministic offset from
    # the same stream. The offset is public and is not a secret key.
    ciphertext = bytearray(n)
    following = iv
    for i in range(n - 1, -1, -1):
        ciphertext[i] = (forward[i] + stream[i] + following) & 0xFF
        following = ciphertext[i]

    return bytes(ciphertext)


def decrypt(data, x0=1.0, y0=1.0, z0=1.0, warmup=100, iv=0):
    ciphertext = _validate_data(data)

    if not isinstance(iv, int) or not 0 <= iv <= 255:
        raise ValueError("iv must be an integer from 0 to 255")
    if not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a non-negative integer")

    n = len(ciphertext)
    if n == 0:
        return b""

    permutation, stream = _make_schedule(
        n, x0, y0, z0, warmup
    )

    # Reverse the reverse-direction pass.
    forward = bytearray(n)
    following = iv
    for i in range(n - 1, -1, -1):
        forward[i] = (ciphertext[i] - stream[i] - following) & 0xFF
        following = ciphertext[i]

    # Reverse the forward-direction pass.
    permuted = bytearray(n)
    previous = iv
    for i in range(n):
        permuted[i] = (forward[i] - stream[i] - previous) & 0xFF
        previous = forward[i]

    plaintext = bytearray(n)
    for i, source_index in enumerate(permutation):
        plaintext[source_index] = permuted[i]

    return bytes(plaintext)
