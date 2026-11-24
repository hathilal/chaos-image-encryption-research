
"""Reproducible 1-LSB key-sensitivity experiment.

Research baseline only; statistical sensitivity does not establish security.
"""

import csv
import json
from pathlib import Path

from chaos_cipher.cipher import encrypt, decrypt
from chaos_cipher.fixed_point import from_float, to_float
from chaos_cipher.metrics import npcr, uaci


WIDTH = 128
HEIGHT = 128
PIXEL_COUNT = WIDTH * HEIGHT
BASE_X0 = 1.0
Y0 = 1.0
Z0 = 1.0
WARMUP = 100


def make_test_image(width=WIDTH, height=HEIGHT):
    """Create a deterministic grayscale test image."""
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive")

    return bytes(
        (x * 3 + y * 5) & 0xFF
        for y in range(height)
        for x in range(width)
    )


def make_one_lsb_key_pair(x0=BASE_X0):
    """Return two x0 values whose Q16.16 representations differ by 1 LSB."""
    base_q = from_float(x0)
    changed_q = base_q ^ 1

    base_value = to_float(base_q)
    changed_value = to_float(changed_q)

    # Guard against accidental multi-bit or rounded-away changes.
    if from_float(changed_value) != changed_q:
        raise AssertionError("Perturbed key did not survive Q16.16 conversion")
    if (base_q ^ changed_q) != 1:
        raise AssertionError("Key representations do not differ by one LSB")

    return base_value, changed_value


def run_key_sensitivity(plaintext):
    """Encrypt the same plaintext under two keys differing by one x0 LSB."""
    plaintext = bytes(plaintext)
    if not plaintext:
        raise ValueError("Plaintext must not be empty")

    base_x0, changed_x0 = make_one_lsb_key_pair(BASE_X0)

    cipher_base = encrypt(
        plaintext, x0=base_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )
    cipher_changed = encrypt(
        plaintext, x0=changed_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )

    changed_bytes = sum(
        a != b for a, b in zip(cipher_base, cipher_changed)
    )

    recovered_base = decrypt(
        cipher_base, x0=base_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )
    recovered_changed = decrypt(
        cipher_changed, x0=changed_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )

    return {
        "experiment": "Q16.16 x0 one-LSB key sensitivity",
        "image_width": WIDTH if len(plaintext) == PIXEL_COUNT else None,
        "image_height": HEIGHT if len(plaintext) == PIXEL_COUNT else None,
        "plaintext_bytes": len(plaintext),
        "fixed_point_format": "signed Q16.16",
        "base_x0": base_x0,
        "perturbed_x0": changed_x0,
        "base_x0_q16_16": from_float(base_x0),
        "perturbed_x0_q16_16": from_float(changed_x0),
        "fixed_point_lsb_difference": abs(
            from_float(base_x0) - from_float(changed_x0)
        ),
        "warmup_iterations": WARMUP,
        "changed_ciphertext_bytes": changed_bytes,
        "npcr_percent": npcr(cipher_base, cipher_changed),
        "uaci_percent": uaci(cipher_base, cipher_changed),
        "baseline_exact_recovery": recovered_base == plaintext,
        "perturbed_key_exact_recovery": recovered_changed == plaintext,
        "ciphertexts_identical": cipher_base == cipher_changed,
        "interpretation": (
            "One-LSB sensitivity measurement for the XOR baseline; "
            "not a cryptographic security proof."
        ),
    }


def save_report(result, output_dir="reports"):
    """Save a JSON report and a compact CSV summary."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    json_path = directory / "key_sensitivity.json"
    csv_path = directory / "key_sensitivity.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
        file.write("\n")

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)

    return json_path, csv_path


def main():
    plaintext = make_test_image()
    result = run_key_sensitivity(plaintext)
    json_path, csv_path = save_report(result)

    print("=== 1-LSB KEY-SENSITIVITY EXPERIMENT ===")
    print(f"Plaintext size: {result['plaintext_bytes']} bytes")
    print(f"Base x0 (Q16.16): {result['base_x0_q16_16']}")
    print(f"Changed x0 (Q16.16): {result['perturbed_x0_q16_16']}")
    print(f"Fixed-point LSB difference: {result['fixed_point_lsb_difference']}")
    print(f"Changed ciphertext bytes: {result['changed_ciphertext_bytes']}")
    print(f"NPCR: {result['npcr_percent']:.6f}%")
    print(f"UACI: {result['uaci_percent']:.6f}%")
    print(f"Baseline exact recovery: {result['baseline_exact_recovery']}")
    print(f"Perturbed-key exact recovery: {result['perturbed_key_exact_recovery']}")
    print(f"Ciphertexts identical: {result['ciphertexts_identical']}")
    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")
    print()
    print("Note: high NPCR/UACI alone do not establish cryptographic security.")

    if not (
        result["baseline_exact_recovery"]
        and result["perturbed_key_exact_recovery"]
    ):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
