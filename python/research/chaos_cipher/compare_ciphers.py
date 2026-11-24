"""Compare the XOR baseline and permutation-diffusion prototype."""

import csv
import json
import time
from pathlib import Path

from chaos_cipher.cipher import encrypt as xor_encrypt
from chaos_cipher.cipher import decrypt as xor_decrypt
from chaos_cipher.permutation_diffusion import encrypt as pd_encrypt
from chaos_cipher.permutation_diffusion import decrypt as pd_decrypt
from chaos_cipher.metrics import npcr, uaci

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def make_test_image(width=128, height=128):
    """Deterministic synthetic grayscale image."""
    return bytes(
        (x * 3 + y * 5 + ((x * y) % 251)) & 0xFF
        for y in range(height)
        for x in range(width)
    )


def adjacent_correlation(data, width, height):
    """Pearson correlation of horizontally adjacent pixels."""
    if len(data) != width * height:
        raise ValueError("Data length does not match dimensions")

    left = [data[y * width + x] for y in range(height)
            for x in range(width - 1)]
    right = [data[y * width + x + 1] for y in range(height)
             for x in range(width - 1)]

    n = len(left)
    mean_l = sum(left) / n
    mean_r = sum(right) / n
    var_l = sum((v - mean_l) ** 2 for v in left)
    var_r = sum((v - mean_r) ** 2 for v in right)

    if var_l == 0 or var_r == 0:
        return 0.0

    cov = sum((a - mean_l) * (b - mean_r)
              for a, b in zip(left, right))
    return cov / (var_l * var_r) ** 0.5


def histogram_summary(data):
    counts = [0] * 256
    for value in data:
        counts[value] += 1

    expected = len(data) / 256
    chi_square = sum((count - expected) ** 2 / expected
                     for count in counts) if expected else 0.0

    return {
        "unique_values": sum(count > 0 for count in counts),
        "histogram_chi_square": round(chi_square, 6),
    }


def timed_encrypt_decrypt(encrypt_fn, decrypt_fn, plaintext, **kwargs):
    start = time.perf_counter()
    ciphertext = encrypt_fn(plaintext, **kwargs)
    encryption_seconds = time.perf_counter() - start

    start = time.perf_counter()
    recovered = decrypt_fn(ciphertext, **kwargs)
    decryption_seconds = time.perf_counter() - start

    return ciphertext, recovered, encryption_seconds, decryption_seconds


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    plaintext = make_test_image()
    changed_key_x0 = 1.0 + 1.0 / 65536.0

    implementations = {
        "xor_baseline": (xor_encrypt, xor_decrypt),
        "permutation_diffusion": (pd_encrypt, pd_decrypt),
    }

    results = []

    for name, (encrypt_fn, decrypt_fn) in implementations.items():
        kwargs = {"x0": 1.0, "y0": 1.0, "z0": 1.0, "warmup": 100}

        ciphertext, recovered, enc_s, dec_s = timed_encrypt_decrypt(
            encrypt_fn, decrypt_fn, plaintext, **kwargs
        )

        perturbed = encrypt_fn(
            plaintext,
            x0=changed_key_x0,
            y0=1.0,
            z0=1.0,
            warmup=100,
        )

        result = {
            "cipher": name,
            "image_width": 128,
            "image_height": 128,
            "plaintext_bytes": len(plaintext),
            "ciphertext_bytes": len(ciphertext),
            "exact_recovery": recovered == plaintext,
            "ciphertexts_differ_under_one_lsb_key_change":
                ciphertext != perturbed,
            "npcr_key_change_percent": round(npcr(ciphertext, perturbed), 6),
            "uaci_key_change_percent": round(uaci(ciphertext, perturbed), 6),
            "plaintext_horizontal_correlation":
                round(adjacent_correlation(plaintext, 128, 128), 6),
            "ciphertext_horizontal_correlation":
                round(adjacent_correlation(ciphertext, 128, 128), 6),
            "encryption_seconds": round(enc_s, 6),
            "decryption_seconds": round(dec_s, 6),
            **histogram_summary(ciphertext),
        }
        results.append(result)

    json_path = REPORTS / "cipher_comparison.json"
    csv_path = REPORTS / "cipher_comparison.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print("CIPHER COMPARISON — 128 x 128 GRAYSCALE")
    print("=" * 72)

    for result in results:
        print(f"\n{result['cipher']}")
        for key, value in result.items():
            if key != "cipher":
                print(f"  {key}: {value}")

    print(f"\nJSON report: {json_path}")
    print(f"CSV report:  {csv_path}")


if __name__ == "__main__":
    main()