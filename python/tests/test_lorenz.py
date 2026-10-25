"""Unit tests for the floating-point Lorenz/RK2 reference model."""

import math
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chaos_image_encryption import (  # noqa: E402
    LorenzParameters,
    LorenzState,
    lorenz_derivative,
    rk2_midpoint_step,
    simulate_lorenz,
)


class TestLorenzModel(unittest.TestCase):
    def test_derivative_at_origin_is_zero(self):
        derivative = lorenz_derivative(LorenzState(0.0, 0.0, 0.0))
        self.assertEqual(derivative, LorenzState(0.0, 0.0, 0.0))

    def test_known_derivative(self):
        # At (1, 1, 1), sigma=10, rho=28, beta=8/3:
        # dx=0, dy=26, dz=1-8/3=-5/3.
        derivative = lorenz_derivative(LorenzState(1.0, 1.0, 1.0))
        self.assertAlmostEqual(derivative.x, 0.0)
        self.assertAlmostEqual(derivative.y, 26.0)
        self.assertAlmostEqual(derivative.z, -5.0 / 3.0)

    def test_rk2_step_is_finite(self):
        state = rk2_midpoint_step(LorenzState(1.0, 1.0, 1.0), 0.01)
        for value in state.as_tuple():
            self.assertTrue(math.isfinite(value))

    def test_simulation_includes_initial_state(self):
        initial = LorenzState(1.0, 1.0, 1.0)
        states = simulate_lorenz(initial, steps=10, step_size=0.01)
        self.assertEqual(len(states), 11)
        self.assertEqual(states[0], initial)

    def test_zero_steps_returns_only_initial_state(self):
        initial = LorenzState(1.0, 2.0, 3.0)
        self.assertEqual(simulate_lorenz(initial, steps=0), [initial])

    def test_invalid_step_size_rejected(self):
        with self.assertRaises(ValueError):
            rk2_midpoint_step(LorenzState(1.0, 1.0, 1.0), 0.0)

    def test_negative_step_count_rejected(self):
        with self.assertRaises(ValueError):
            simulate_lorenz(LorenzState(1.0, 1.0, 1.0), steps=-1)

    def test_custom_parameters_are_used(self):
        params = LorenzParameters(sigma=1.0, rho=2.0, beta=1.0)
        derivative = lorenz_derivative(LorenzState(1.0, 2.0, 3.0), params)
        self.assertEqual(derivative.x, 1.0)
        self.assertEqual(derivative.y, -3.0)
        self.assertEqual(derivative.z, -1.0)


if __name__ == "__main__":
    unittest.main()
