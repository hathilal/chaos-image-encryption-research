
import unittest

from chaos_cipher.fixed_point import from_float
from chaos_cipher.key_sensitivity import (
    make_one_lsb_key_pair,
    make_test_image,
    run_key_sensitivity,
)


class TestKeySensitivity(unittest.TestCase):
    def test_key_pair_differs_by_exactly_one_lsb(self):
        base, changed = make_one_lsb_key_pair(1.0)
        base_q = from_float(base)
        changed_q = from_float(changed)

        self.assertEqual(base_q ^ changed_q, 1)
        self.assertEqual(abs(base_q - changed_q), 1)

    def test_perturbed_key_is_reproducible(self):
        first = make_one_lsb_key_pair(1.0)
        second = make_one_lsb_key_pair(1.0)
        self.assertEqual(first, second)

    def test_test_image_dimensions(self):
        image = make_test_image()
        self.assertEqual(len(image), 128 * 128)

    def test_empty_plaintext_rejected(self):
        with self.assertRaises(ValueError):
            run_key_sensitivity(b"")

    def test_both_keys_recover_plaintext(self):
        plaintext = make_test_image(width=8, height=8)
        result = run_key_sensitivity(plaintext)

        self.assertTrue(result["baseline_exact_recovery"])
        self.assertTrue(result["perturbed_key_exact_recovery"])

    def test_metrics_are_in_valid_ranges(self):
        plaintext = bytes(range(256))
        result = run_key_sensitivity(plaintext)

        self.assertGreaterEqual(result["npcr_percent"], 0.0)
        self.assertLessEqual(result["npcr_percent"], 100.0)
        self.assertGreaterEqual(result["uaci_percent"], 0.0)
        self.assertLessEqual(result["uaci_percent"], 100.0)

    def test_fixed_point_difference_reported_as_one(self):
        result = run_key_sensitivity(bytes(range(64)))
        self.assertEqual(result["fixed_point_lsb_difference"], 1)


if __name__ == "__main__":
    unittest.main()
