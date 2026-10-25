"""Bit-accurate fixed-point Lorenz/RK2 model.

The model stores signed two's-complement raw integers. A value is interpreted
as raw / 2**fractional_bits. Each multiply keeps the full integer product,
then uses an arithmetic right shift to restore the Q scale. Results are
checked or wrapped to the configured signed word width after each modeled
storage point. This operation order is part of the model contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .lorenz import LorenzParameters

OverflowPolicy = Literal["raise", "wrap"]


@dataclass(frozen=True)
class FixedPointFormat:
    """Signed fixed-point format; defaults to 32-bit with 19 fractional bits."""

    width: int = 32
    fractional_bits: int = 19
    overflow_policy: OverflowPolicy = "raise"

    def __post_init__(self) -> None:
        if self.width < 2:
            raise ValueError("width must be at least 2 bits")
        if not 0 <= self.fractional_bits < self.width:
            raise ValueError("fractional_bits must be in [0, width)")
        if self.overflow_policy not in ("raise", "wrap"):
            raise ValueError("overflow_policy must be 'raise' or 'wrap'")

    @property
    def scale(self) -> int:
        return 1 << self.fractional_bits

    @property
    def min_raw(self) -> int:
        return -(1 << (self.width - 1))

    @property
    def max_raw(self) -> int:
        return (1 << (self.width - 1)) - 1

    @property
    def min_value(self) -> float:
        return self.min_raw / self.scale

    @property
    def max_value(self) -> float:
        return self.max_raw / self.scale

    def from_float(self, value: float) -> int:
        """Quantize using round-to-nearest, ties away from zero."""
        scaled = value * self.scale
        raw = int(scaled + 0.5) if scaled >= 0 else int(scaled - 0.5)
        return self.store(raw)

    def to_float(self, raw: int) -> float:
        return raw / self.scale

    def store(self, raw: int) -> int:
        """Apply the configured overflow behavior at a storage boundary."""
        if self.min_raw <= raw <= self.max_raw:
            return raw
        if self.overflow_policy == "raise":
            raise OverflowError(
                f"raw fixed-point value {raw} outside "
                f"[{self.min_raw}, {self.max_raw}]"
            )
        modulus = 1 << self.width
        wrapped = raw % modulus
        if wrapped >= (1 << (self.width - 1)):
            wrapped -= modulus
        return wrapped


@dataclass(frozen=True)
class FixedPointState:
    """Raw integer state (x, y, z), all in the same fixed-point format."""

    x: int
    y: int
    z: int

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)


class FixedPointLorenz:
    """Lorenz equations integrated with explicit midpoint RK2."""

    def __init__(
        self,
        fmt: FixedPointFormat = FixedPointFormat(),
        parameters: LorenzParameters = LorenzParameters(),
    ) -> None:
        self.fmt = fmt
        self.sigma = fmt.from_float(parameters.sigma)
        self.rho = fmt.from_float(parameters.rho)
        self.beta = fmt.from_float(parameters.beta)

    def state_from_floats(self, x: float, y: float, z: float) -> FixedPointState:
        return FixedPointState(
            self.fmt.from_float(x),
            self.fmt.from_float(y),
            self.fmt.from_float(z),
        )

    def state_to_floats(self, state: FixedPointState) -> tuple[float, float, float]:
        return tuple(self.fmt.to_float(v) for v in state.as_tuple())  # type: ignore[return-value]

    def _add(self, a: int, b: int) -> int:
        return self.fmt.store(a + b)

    def _sub(self, a: int, b: int) -> int:
        return self.fmt.store(a - b)

    def _mul(self, a: int, b: int) -> int:
        # Python's right shift is arithmetic for negative integers (rounds down).
        return self.fmt.store((a * b) >> self.fmt.fractional_bits)

    def derivative(self, state: FixedPointState) -> FixedPointState:
        x, y, z = state.as_tuple()
        dx = self._mul(self.sigma, self._sub(y, x))
        rho_minus_z = self._sub(self.rho, z)
        dy = self._sub(self._mul(x, rho_minus_z), y)
        dz = self._sub(self._mul(x, y), self._mul(self.beta, z))
        return FixedPointState(dx, dy, dz)

    def rk2_midpoint_step(self, state: FixedPointState, step_size: float = 0.01) -> FixedPointState:
        """Advance one midpoint-RK2 step with quantization at each operation."""
        if step_size <= 0.0:
            raise ValueError("step_size must be positive")
        h = self.fmt.from_float(step_size)
        half_h = h >> 1
        k1 = self.derivative(state)
        midpoint = FixedPointState(
            self._add(state.x, self._mul(half_h, k1.x)),
            self._add(state.y, self._mul(half_h, k1.y)),
            self._add(state.z, self._mul(half_h, k1.z)),
        )
        k2 = self.derivative(midpoint)
        return FixedPointState(
            self._add(state.x, self._mul(h, k2.x)),
            self._add(state.y, self._mul(h, k2.y)),
            self._add(state.z, self._mul(h, k2.z)),
        )

    def simulate(
        self,
        initial_state: FixedPointState,
        steps: int,
        step_size: float = 0.01,
    ) -> list[FixedPointState]:
        """Return steps + 1 states, including the initial state."""
        if steps < 0:
            raise ValueError("steps must be non-negative")
        states = [initial_state]
        state = initial_state
        for _ in range(steps):
            state = self.rk2_midpoint_step(state, step_size)
            states.append(state)
        return states
