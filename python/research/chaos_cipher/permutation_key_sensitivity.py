"""One-LSB key-sensitivity experiment for permutation-diffusion."""

import csv
import json
from pathlib import Path

from chaos_cipher.fixed_point import from_float, to_float
from chaos_cipher.metrics import npcr, uaci
from chaos_cipher.permutation_diffusion import encrypt, decrypt

WIDTH = 128
HEIGHT = 128
BASE_X0 = 1.0
Y0 = 1.0
Z0 = 1.0
WARMUP = 100
IV = 0


def make_test_image():
    return bytes(
        (x * 3 + y * 5) & 0xFF
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )


def run_experiment(plaintext):
    base_q = from_float(BASE_X0)
    changed_q = base_q ^ 1
    base_x0 = to_float(base_q)
    changed_x0 = to_float(changed_q)

    if from_float(changed_x0) != changed_q:
        raise AssertionError("Perturbed key failed Q16.16 round-trip")

    common = {
        "y0": Y0,
        "z0": Z0,
        "warmup": WARMUP,
        "iv": IV,
    }

    cipher_base = encrypt(plaintext, x0=base_x0, **common)
    cipher_changed = encrypt(plaintext, x0=changed_x0, **common)

    recovered_base = decrypt(cipher_base, x0=base_x0, **common)
    recovered_changed = decrypt(cipher_changed, x0=changed_x0, **common)

    changed_bytes = sum(
        a != b for a, b in zip(cipher_base, cipher_changed)
    )

    return {
        "experiment": "Permutation-diffusion Q16.16 x0 one-LSB sensitivity",
        "image_width": WIDTH,
        "image_height": HEIGHT,
        "plaintext_bytes": len(plaintext),
        "fixed_point_format": "signed Q16.16",
        "base_x0": base_x0,
        "perturbed_x0": changed_x0,
        "base_x0_q16_16": base_q,
        "perturbed_x0_q16_16": changed_q,
        "fixed_point_lsb_difference": abs(base_q - changed_q),
        "warmup_iterations": WARMUP,
        "iv": IV,
        "changed_ciphertext_bytes": changed_bytes,
        "npcr_percent": npcr(cipher_base, cipher_changed),
        "uaci_percent": uaci(cipher_base, cipher_changed),
        "baseline_exact_recovery": recovered_base == plaintext,
        "perturbed_key_exact_recovery": recovered_changed == plaintext,
        "ciphertexts_identical": cipher_base == cipher_changed,
        "interpretation": (
            "One-LSB sensitivity measurement for the permutation-diffusion "
            "prototype; not a cryptographic security proof."
        ),
    }


def main():
    plaintext = make_test_image()
    result = run_experiment(plaintext)

    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "permutation_key_sensitivity.json"
    csv_path = output_dir / "permutation_key_sensitivity.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)

    print("=== PERMUTATION-DIFFUSION 1-LSB KEY SENSITIVITY ===")
    print(f"Plaintext size: {result['plaintext_bytes']} bytes")
    print(f"Base x0 (Q16.16): {result['base_x0_q16_16']}")
    print(f"Changed x0 (Q16.16): {result['perturbed_x0_q16_16']}")
    print(f"Fixed-point LSB difference: {result['fixed_point_lsb_difference']}")
    print(f"Changed ciphertext bytes: {result['changed_ciphertext_bytes']}")
    print(f"NPCR: {result['npcr_percent']:.6f}%")
    print(f"UACI: {result['uaci_percent']:.6f}%")
    print(f"Base-key exact recovery: {result['baseline_exact_recovery']}")
    print(f"Perturbed-key exact recovery: {result['perturbed_key_exact_recovery']}")
    print(f"Ciphertexts identical: {result['ciphertexts_identical']}")
    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")
    print("Note: high NPCR/UACI alone do not establish cryptographic security.")

    if not (
        result["baseline_exact_recovery"]
        and result["perturbed_key_exact_recovery"]
    ):
        raise SystemExit("ERROR: exact recovery failed")


if __name__ == "__main__":
    main()
