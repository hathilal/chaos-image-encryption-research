"""Tests for the bit-accurate fixed-point Lorenz model."""

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chaos_image_encryption import (  # noqa: E402
    FixedPointFormat,
    FixedPointLorenz,
    FixedPointState,
    LorenzState,
    rk2_midpoint_step,
)


class TestFixedPointFormat(unittest.TestCase):
    def test_default_format_range_and_resolution(self):
        fmt = FixedPointFormat()
        self.assertEqual(fmt.scale, 1 << 19)
        self.assertEqual(fmt.min_raw, -(1 << 31))
        self.assertEqual(fmt.max_raw, (1 << 31) - 1)
        self.assertEqual(fmt.min_value, -4096.0)
        self.assertLess(fmt.max_value, 4096.0)

    def test_round_trip_quantization(self):
        fmt = FixedPointFormat()
        raw = fmt.from_float(1.25)
        self.assertEqual(raw, 1.25 * fmt.scale)
        self.assertEqual(fmt.to_float(raw), 1.25)

    def test_ties_round_away_from_zero(self):
        fmt = FixedPointFormat(width=8, fractional_bits=2)
        self.assertEqual(fmt.from_float(0.125), 1)
        self.assertEqual(fmt.from_float(-0.125), -1)

    def test_overflow_raises_by_default(self):
        fmt = FixedPointFormat(width=8, fractional_bits=4)
        with self.assertRaises(OverflowError):
            fmt.from_float(8.0)

    def test_overflow_can_wrap_like_twos_complement_hardware(self):
        fmt = FixedPointFormat(width=8, fractional_bits=4, overflow_policy="wrap")
        self.assertEqual(fmt.from_float(8.0), -128)


class TestFixedPointLorenz(unittest.TestCase):
    def setUp(self):
        self.model = FixedPointLorenz()
        self.initial = self.model.state_from_floats(1.0, 1.0, 1.0)

    def test_derivative_matches_known_values_with_quantization(self):
        derivative = self.model.derivative(self.initial)
        dx, dy, dz = self.model.state_to_floats(derivative)
        self.assertAlmostEqual(dx, 0.0, places=5)
        self.assertAlmostEqual(dy, 26.0, places=4)
        self.assertAlmostEqual(dz, -5.0 / 3.0, places=4)

    def test_rk2_step_is_close_to_float_reference_for_one_step(self):
        fixed_state = self.model.rk2_midpoint_step(self.initial, 0.01)
        fixed_values = self.model.state_to_floats(fixed_state)
        float_state = rk2_midpoint_step(LorenzState(1.0, 1.0, 1.0), 0.01)
        for actual, expected in zip(fixed_values, float_state.as_tuple()):
            self.assertAlmostEqual(actual, expected, delta=0.001)

    def test_simulation_includes_initial_state(self):
        states = self.model.simulate(self.initial, steps=10)
        self.assertEqual(len(states), 11)
        self.assertEqual(states[0], self.initial)

    def test_zero_steps_returns_initial_state(self):
        self.assertEqual(self.model.simulate(self.initial, steps=0), [self.initial])

    def test_negative_steps_rejected(self):
        with self.assertRaises(ValueError):
            self.model.simulate(self.initial, steps=-1)

    def test_nonpositive_step_size_rejected(self):
        with self.assertRaises(ValueError):
            self.model.rk2_midpoint_step(self.initial, 0.0)

    def test_raw_state_can_be_used_directly(self):
        state = FixedPointState(*self.initial.as_tuple())
        self.assertEqual(state, self.initial)


if __name__ == "__main__":
    unittest.main()
