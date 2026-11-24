
"""Fixed-point Lorenz chaotic system using RK2 midpoint integration."""

from chaos_cipher.fixed_point import (
    from_float,
    q_add,
    q_sub,
    q_mul,
    q_div2,
)

# Standard Lorenz system parameters in Q16.16
SIGMA = from_float(10.0)
RHO = from_float(28.0)
BETA = from_float(8.0 / 3.0)

# Integration step size h = 0.01
H = from_float(0.01)
HALF_H = q_div2(H)


def lorenz_rhs(x: int, y: int, z: int) -> tuple[int, int, int]:
    """Return the Lorenz derivatives dx/dt, dy/dt, dz/dt."""
    dx = q_mul(SIGMA, q_sub(y, x))

    dy = q_sub(
        q_mul(x, q_sub(RHO, z)),
        y,
    )

    dz = q_sub(
        q_mul(x, y),
        q_mul(BETA, z),
    )

    return dx, dy, dz


def rk2_step(x: int, y: int, z: int) -> tuple[int, int, int]:
    """Advance the state by one RK2 midpoint integration step."""
    # First derivative at the current state
    k1x, k1y, k1z = lorenz_rhs(x, y, z)

    # Estimate the state at the midpoint
    mid_x = q_add(x, q_mul(HALF_H, k1x))
    mid_y = q_add(y, q_mul(HALF_H, k1y))
    mid_z = q_add(z, q_mul(HALF_H, k1z))

    # Second derivative at the midpoint
    k2x, k2y, k2z = lorenz_rhs(mid_x, mid_y, mid_z)

    # Advance using the midpoint derivative
    next_x = q_add(x, q_mul(H, k2x))
    next_y = q_add(y, q_mul(H, k2y))
    next_z = q_add(z, q_mul(H, k2z))

    return next_x, next_y, next_z
