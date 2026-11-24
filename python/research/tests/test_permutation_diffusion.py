import unittest

from chaos_cipher.permutation_diffusion import encrypt, decrypt


class TestPermutationDiffusion(unittest.TestCase):

    def test_round_trip(self):
        original = bytes(range(256)) * 4
        ciphertext = encrypt(original)
        self.assertEqual(decrypt(ciphertext), original)

    def test_empty_data(self):
        self.assertEqual(encrypt(b""), b"")
        self.assertEqual(decrypt(b""), b"")

    def test_ciphertext_length(self):
        original = bytes(range(100))
        self.assertEqual(len(encrypt(original)), len(original))

    def test_reproducible_encryption(self):
        original = bytes(range(256))
        self.assertEqual(encrypt(original), encrypt(original))

    def test_wrong_initial_condition_changes_ciphertext(self):
        original = bytes(range(256)) * 4
        first = encrypt(original, x0=1.0)
        second = encrypt(original, x0=1.0000152587890625)
        self.assertNotEqual(first, second)

    def test_decrypt_with_same_parameters(self):
        original = b"research prototype test data"
        encrypted = encrypt(
            original, x0=2.0, y0=1.0, z0=1.0,
            warmup=50, iv=17
        )
        recovered = decrypt(
            encrypted, x0=2.0, y0=1.0, z0=1.0,
            warmup=50, iv=17
        )
        self.assertEqual(recovered, original)

    def test_invalid_iv(self):
        with self.assertRaises(ValueError):
            encrypt(b"abc", iv=256)

    def test_negative_warmup(self):
        with self.assertRaises(ValueError):
            encrypt(b"abc", warmup=-1)

    def test_rejects_string_input(self):
        with self.assertRaises(TypeError):
            encrypt("not bytes")


if __name__ == "__main__":
    unittest.main()
