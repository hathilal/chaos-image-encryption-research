
import unittest

from chaos_cipher.metrics import (
    histogram,
    histogram_summary,
    pearson_correlation,
    adjacent_correlations,
    npcr,
    uaci,
)


class TestImageMetrics(unittest.TestCase):
    def test_histogram_counts_pixels(self):
        counts = histogram(bytes([0, 1, 1, 255]))
        self.assertEqual(counts[0], 1)
        self.assertEqual(counts[1], 2)
        self.assertEqual(counts[255], 1)
        self.assertEqual(sum(counts), 4)

    def test_histogram_summary(self):
        result = histogram_summary(bytes([10, 10, 20, 20]))
        self.assertEqual(result["pixel_count"], 4)
        self.assertEqual(result["distinct_values"], 2)
        self.assertAlmostEqual(result["mean"], 15.0)

    def test_perfect_positive_correlation(self):
        result = pearson_correlation([1, 2, 3], [2, 4, 6])
        self.assertAlmostEqual(result, 1.0)

    def test_perfect_negative_correlation(self):
        result = pearson_correlation([1, 2, 3], [6, 4, 2])
        self.assertAlmostEqual(result, -1.0)

    def test_constant_input_correlation_is_defined_as_zero(self):
        result = pearson_correlation([5, 5, 5], [1, 2, 3])
        self.assertEqual(result, 0.0)

    def test_npcr_no_changes(self):
        self.assertAlmostEqual(npcr(bytes([1, 2]), bytes([1, 2])), 0.0)

    def test_npcr_all_changes(self):
        self.assertAlmostEqual(npcr(bytes([1, 2]), bytes([3, 4])), 100.0)

    def test_npcr_one_of_four_changes(self):
        self.assertAlmostEqual(
            npcr(bytes([1, 2, 3, 4]), bytes([1, 9, 3, 4])),
            25.0,
        )

    def test_uaci_no_changes(self):
        self.assertAlmostEqual(uaci(bytes([0, 100]), bytes([0, 100])), 0.0)

    def test_uaci_maximum_difference(self):
        self.assertAlmostEqual(uaci(bytes([0, 0]), bytes([255, 255])), 100.0)

    def test_adjacent_correlations_check_dimensions(self):
        with self.assertRaises(ValueError):
            adjacent_correlations(bytes([1, 2, 3]), 2, 2)

    def test_metrics_reject_unequal_lengths(self):
        with self.assertRaises(ValueError):
            npcr(bytes([1, 2]), bytes([1]))

        with self.assertRaises(ValueError):
            uaci(bytes([1, 2]), bytes([1]))


if __name__ == "__main__":
    unittest.main()
