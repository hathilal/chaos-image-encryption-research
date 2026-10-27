"""Tests for the research image-cipher baseline."""
import unittest

from chaos_image_encryption.image_cipher import ChaosKey, decrypt_image, encrypt_image


class ImageCipherTests(unittest.TestCase):
    def test_round_trip_128_by_128_pattern(self):
        plain = bytes((i * 37 + i // 11) & 0xFF for i in range(128 * 128))
        cipher = encrypt_image(plain, 128, 128, warmup_steps=50)
        self.assertEqual(len(cipher), len(plain))
        self.assertNotEqual(cipher, plain)
        self.assertEqual(decrypt_image(cipher, 128, 128, warmup_steps=50), plain)

    def test_round_trip_small_image(self):
        plain = bytes([0, 1, 2, 3, 127, 128, 254, 255, 9])
        cipher = encrypt_image(plain, 3, 3, warmup_steps=10)
        self.assertEqual(decrypt_image(cipher, 3, 3, warmup_steps=10), plain)

    def test_deterministic_for_same_key(self):
        plain = bytes(range(64))
        a = encrypt_image(plain, 8, 8, warmup_steps=10)
        b = encrypt_image(plain, 8, 8, warmup_steps=10)
        self.assertEqual(a, b)

    def test_different_key_changes_ciphertext(self):
        plain = bytes((i * 13) & 0xFF for i in range(256))
        a = encrypt_image(plain, 16, 16, ChaosKey(x=0.1), warmup_steps=20)
        b = encrypt_image(plain, 16, 16, ChaosKey(x=0.11), warmup_steps=20)
        self.assertNotEqual(a, b)

    def test_rejects_wrong_image_length(self):
        with self.assertRaises(ValueError):
            encrypt_image(bytes(10), 3, 3)

    def test_rejects_nonpositive_dimensions(self):
        with self.assertRaises(ValueError):
            encrypt_image(bytes(0), 0, 1)

    def test_rejects_negative_warmup(self):
        with self.assertRaises(ValueError):
            encrypt_image(bytes([1]), 1, 1, warmup_steps=-1)

    def test_rejects_nonpositive_step_size(self):
        with self.assertRaises(ValueError):
            encrypt_image(bytes([1]), 1, 1, step_size=0)


if __name__ == "__main__":
    unittest.main()
