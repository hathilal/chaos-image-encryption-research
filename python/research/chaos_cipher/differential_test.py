
"""Differential-encryption experiment for the current XOR baseline."""

from chaos_cipher.cipher import encrypt
from chaos_cipher.metrics import npcr, uaci


WIDTH = 128
HEIGHT = 128
PIXEL_COUNT = WIDTH * HEIGHT


def main():
    # Deterministic test image; no external image files are required.
    plain_a = bytes(
        (x * 3 + y * 5) & 0xFF
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )

    # Change exactly one pixel by one intensity level.
    changed = bytearray(plain_a)
    changed[(HEIGHT // 2) * WIDTH + (WIDTH // 2)] ^= 0x01
    plain_b = bytes(changed)

    # Same key and same cipher settings for both plaintexts.
    # Verify encrypt() argument order in cipher.py if this errors.
    cipher_a = encrypt(plain_a)
    cipher_b = encrypt(plain_b)

    print("Differential-encryption experiment")
    print(f"Image dimensions: {WIDTH} x {HEIGHT}")
    print("Plaintext difference: 1 pixel, 1-bit change")
    print(f"Plaintexts differ at {sum(a != b for a, b in zip(plain_a, plain_b))} byte(s)")
    print(f"Ciphertexts differ at {sum(a != b for a, b in zip(cipher_a, cipher_b))} byte(s)")
    print(f"NPCR: {npcr(cipher_a, cipher_b):.6f}%")
    print(f"UACI: {uaci(cipher_a, cipher_b):.6f}%")
    print()
    print("Interpretation: the current XOR baseline is expected to change")
    print("only the corresponding ciphertext byte when the keystream is fixed.")
    print("This experiment measures a baseline, not cryptographic security.")


if __name__ == "__main__":
    main()
