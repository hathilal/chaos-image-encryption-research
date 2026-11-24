
import unittest

from chaos_cipher.cipher import encrypt, decrypt


class TestCipher(unittest.TestCase):
    def test_round_trip(self):
        original = bytes(range(256))
        encrypted = encrypt(original)
        recovered = decrypt(encrypted)
        self.assertEqual(recovered, original)

    def test_empty_data(self):
        self.assertEqual(encrypt(b""), b"")
        self.assertEqual(decrypt(b""), b"")

    def test_ciphertext_length(self):
        original = b"test image data"
        self.assertEqual(len(encrypt(original)), len(original))

    def test_wrong_initial_condition_changes_output(self):
        original = b"A small test message for encryption."
        correct = encrypt(original)
        wrong = decrypt(correct, x0=1.001)
        self.assertNotEqual(wrong, original)


if __name__ == "__main__":
    unittest.main()
