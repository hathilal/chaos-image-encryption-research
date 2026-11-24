"""Experimental permutation-diffusion image cipher.

Research prototype for comparison with the existing XOR baseline.
Not a production-secure encryption algorithm.
"""

from chaos_cipher.keystream import generate_keystream


def _validate_data(data):
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")
    return bytes(data)


def _make_schedule(length, x0, y0, z0, warmup):
    """Generate a deterministic permutation and diffusion byte stream."""
    if length == 0:
        return [], b""

    # Generate extra bytes to derive the permutation ranks.
    stream = generate_keystream(
        length * 2,
        x0=x0,
        y0=y0,
        z0=z0,
        warmup=warmup,
    )

    # Sort indices by their derived rank, using index as a tie-breaker.
    # Sorting a deterministic rank sequence yields a reproducible permutation.
    ranks = [
        (stream[i] << 8) | stream[length + i]
        for i in range(length)
    ]
    permutation = sorted(range(length), key=lambda i: (ranks[i], i))

    diffusion = generate_keystream(
        length,
        x0=x0,
        y0=y0,
        z0=z0,
        warmup=warmup,
    )
    return permutation, diffusion


def encrypt(data, x0=1.0, y0=1.0, z0=1.0, warmup=100, iv=0):
    """Encrypt bytes using permutation followed by chained diffusion."""
    plaintext = _validate_data(data)

    if not 0 <= iv <= 255:
        raise ValueError("iv must be an integer from 0 to 255")
    if not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a non-negative integer")

    length = len(plaintext)
    if length == 0:
        return b""

    permutation, stream = _make_schedule(
        length, x0, y0, z0, warmup
    )

    permuted = bytearray(length)
    for i, source_index in enumerate(permutation):
        permuted[i] = plaintext[source_index]

    ciphertext = bytearray(length)
    previous = iv

    for i, value in enumerate(permuted):
        current = (value + stream[i] + previous) & 0xFF
        ciphertext[i] = current
        previous = current

    return bytes(ciphertext)


def decrypt(data, x0=1.0, y0=1.0, z0=1.0, warmup=100, iv=0):
    """Decrypt bytes produced by encrypt() using the same parameters."""
    ciphertext = _validate_data(data)

    if not 0 <= iv <= 255:
        raise ValueError("iv must be an integer from 0 to 255")
    if not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a non-negative integer")

    length = len(ciphertext)
    if length == 0:
        return b""

    permutation, stream = _make_schedule(
        length, x0, y0, z0, warmup
    )

    permuted_plaintext = bytearray(length)
    previous = iv

    for i, value in enumerate(ciphertext):
        permuted_plaintext[i] = (value - stream[i] - previous) & 0xFF
        previous = value

    plaintext = bytearray(length)
    for i, source_index in enumerate(permutation):
        plaintext[source_index] = permuted_plaintext[i]

    return bytes(plaintext)
