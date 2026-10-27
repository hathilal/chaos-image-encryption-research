"""Research baseline for permutation-diffusion image encryption.

This is an educational, reproducible baseline—not a production cryptographic
cipher. It uses a fixed-point Lorenz trajectory to derive permutation indices
and XOR diffusion bytes. Do not use it to protect sensitive images.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .fixed_point import FixedPointFormat, FixedPointLorenz, FixedPointState
from .lorenz import LorenzParameters

_MASK32 = 0xFFFFFFFF


@dataclass(frozen=True)
class ChaosKey:
    """Secret starting state and Lorenz parameters for reproducible experiments."""

    x: float = 0.1
    y: float = 0.2
    z: float = 0.3
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0

    def parameters(self) -> LorenzParameters:
        return LorenzParameters(self.sigma, self.rho, self.beta)


def _validate_image(image: Sequence[int], width: int, height: int) -> bytes:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if len(image) != width * height:
        raise ValueError("image length must equal width * height")
    try:
        result = bytes(image)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("image pixels must be integers in the range 0..255") from exc
    return result


def _word_from_state(state: FixedPointState) -> int:
    """Mix the three raw state words into a deterministic 32-bit sample."""
    x, y, z = (v & _MASK32 for v in state.as_tuple())
    # Rotate and XOR are simple, hardware-friendly extraction operations.
    y_rot = ((y << 11) | (y >> 21)) & _MASK32
    z_rot = ((z << 17) | (z >> 15)) & _MASK32
    return (x ^ y_rot ^ z_rot) & _MASK32


class _ChaoticWordStream:
    def __init__(
        self,
        key: ChaosKey,
        warmup_steps: int,
        step_size: float,
        fmt: FixedPointFormat,
    ) -> None:
        if warmup_steps < 0:
            raise ValueError("warmup_steps must be non-negative")
        if step_size <= 0:
            raise ValueError("step_size must be positive")
        self.system = FixedPointLorenz(fmt, key.parameters())
        self.state = self.system.state_from_floats(key.x, key.y, key.z)
        for _ in range(warmup_steps):
            self.state = self.system.rk2_midpoint_step(self.state, step_size)
        self.step_size = step_size

    def next_word(self) -> int:
        self.state = self.system.rk2_midpoint_step(self.state, self.step_size)
        return _word_from_state(self.state)


def _permutation(size: int, stream: _ChaoticWordStream) -> list[int]:
    """Fisher-Yates shuffle; result[i] identifies the source pixel for slot i."""
    indices = list(range(size))
    for i in range(size - 1, 0, -1):
        j = stream.next_word() % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]
    return indices


def encrypt_image(
    image: Sequence[int],
    width: int,
    height: int,
    key: ChaosKey = ChaosKey(),
    *,
    warmup_steps: int = 1000,
    step_size: float = 0.01,
    fmt: FixedPointFormat = FixedPointFormat(),
) -> bytes:
    """Encrypt a grayscale image represented by one byte per pixel.

    The image is first permuted, then diffused using chained XOR:
    C[i] = P_perm[i] XOR K[i] XOR C[i-1], with C[-1] = 0.
    """
    plain = _validate_image(image, width, height)
    stream = _ChaoticWordStream(key, warmup_steps, step_size, fmt)
    permutation = _permutation(len(plain), stream)
    permuted = [plain[source_index] for source_index in permutation]

    cipher = bytearray(len(plain))
    previous_cipher = 0
    for i, pixel in enumerate(permuted):
        cipher_byte = pixel ^ (stream.next_word() & 0xFF) ^ previous_cipher
        cipher[i] = cipher_byte
        previous_cipher = cipher_byte
    return bytes(cipher)


def decrypt_image(
    image: Sequence[int],
    width: int,
    height: int,
    key: ChaosKey = ChaosKey(),
    *,
    warmup_steps: int = 1000,
    step_size: float = 0.01,
    fmt: FixedPointFormat = FixedPointFormat(),
) -> bytes:
    """Decrypt an image encrypted by :func:`encrypt_image` with matching settings."""
    cipher = _validate_image(image, width, height)
    stream = _ChaoticWordStream(key, warmup_steps, step_size, fmt)
    permutation = _permutation(len(cipher), stream)

    permuted_plain = bytearray(len(cipher))
    previous_cipher = 0
    for i, cipher_byte in enumerate(cipher):
        permuted_plain[i] = cipher_byte ^ (stream.next_word() & 0xFF) ^ previous_cipher
        previous_cipher = cipher_byte

    plain = bytearray(len(cipher))
    for slot, source_index in enumerate(permutation):
        plain[source_index] = permuted_plain[slot]
    return bytes(plain)
