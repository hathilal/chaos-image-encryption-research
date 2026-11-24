import unittest

from chaos_cipher.fixed_point import from_float, to_float
from chaos_cipher.lorenz import lorenz_rhs, rk2_step


class TestLorenz(unittest.TestCase):
    def test_rhs_at_initial_state(self):
        x = from_float(1.0)
        y = from_float(1.0)
        z = from_float(1.0)

        dx, dy, dz = lorenz_rhs(x, y, z)

        self.assertAlmostEqual(to_float(dx), 0.0, places=3)
        self.assertAlmostEqual(to_float(dy), 26.0, places=2)
        self.assertAlmostEqual(to_float(dz), -1.6667, places=2)

    def test_rk2_returns_three_integers(self):
        state = (from_float(1.0), from_float(1.0), from_float(1.0))
        result = rk2_step(*state)

        self.assertEqual(len(result), 3)
        self.assertTrue(all(isinstance(value, int) for value in result))

    def test_rk2_changes_state(self):
        state = (from_float(1.0), from_float(1.0), from_float(1.0))
        self.assertNotEqual(rk2_step(*state), state)


if __name__ == "__main__":
    unittest.main()