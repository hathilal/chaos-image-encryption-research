
import unittest

from chaos_cipher.keystream import generate_keystream


class TestKeystream(unittest.TestCase):
    def test_requested_length(self):
        self.assertEqual(len(generate_keystream(128)), 128)

    def test_reproducible(self):
        first = generate_keystream(64)
        second = generate_keystream(64)
        self.assertEqual(first, second)

    def test_different_initial_conditions(self):
        first = generate_keystream(64, x0=1.0, y0=1.0, z0=1.0)
        second = generate_keystream(64, x0=1.001, y0=1.0, z0=1.0)
        self.assertNotEqual(first, second)

    def test_empty_stream(self):
        self.assertEqual(generate_keystream(0), b"")

    def test_negative_length_rejected(self):
        with self.assertRaises(ValueError):
            generate_keystream(-1)


if __name__ == "__main__":
    unittest.main()
