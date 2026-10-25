"""Floating-point Lorenz system and explicit midpoint RK2 integrator.

This module is the initial mathematical reference. It is intentionally
floating-point; a separate module will later implement bit-accurate fixed-point
semantics for comparison with RTL.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LorenzParameters:
    """Parameters for the Lorenz system."""

    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0


@dataclass(frozen=True)
class LorenzState:
    """State vector (x, y, z)."""

    x: float
    y: float
    z: float

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


def lorenz_derivative(
    state: LorenzState,
    parameters: LorenzParameters = LorenzParameters(),
) -> LorenzState:
    """Evaluate the Lorenz vector field at ``state``."""
    x, y, z = state.as_tuple()
    sigma, rho, beta = parameters.sigma, parameters.rho, parameters.beta

    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z

    return LorenzState(dx, dy, dz)


def _add_scaled(
    state: LorenzState,
    derivative: LorenzState,
    scale: float,
) -> LorenzState:
    """Return state + scale * derivative."""
    return LorenzState(
        state.x + scale * derivative.x,
        state.y + scale * derivative.y,
        state.z + scale * derivative.z,
    )


def rk2_midpoint_step(
    state: LorenzState,
    step_size: float,
    parameters: LorenzParameters = LorenzParameters(),
) -> LorenzState:
    """Advance the Lorenz state by one explicit midpoint RK2 step.

    k1 = f(X_n)
    X_mid = X_n + (h/2) * k1
    k2 = f(X_mid)
    X_(n+1) = X_n + h * k2
    """
    if step_size <= 0.0:
        raise ValueError("step_size must be positive")

    k1 = lorenz_derivative(state, parameters)
    midpoint = _add_scaled(state, k1, step_size / 2.0)
    k2 = lorenz_derivative(midpoint, parameters)
    return _add_scaled(state, k2, step_size)


def simulate_lorenz(
    initial_state: LorenzState,
    steps: int,
    step_size: float = 0.01,
    parameters: LorenzParameters = LorenzParameters(),
) -> list[LorenzState]:
    """Return ``steps + 1`` states, including the initial state."""
    if steps < 0:
        raise ValueError("steps must be non-negative")

    states = [initial_state]
    state = initial_state
    for _ in range(steps):
        state = rk2_midpoint_step(state, step_size, parameters)
        states.append(state)
    return states
