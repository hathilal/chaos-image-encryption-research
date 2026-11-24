
"""Repeated 1-LSB key-sensitivity trials for research reporting."""

import csv
import json
import statistics
from pathlib import Path

from chaos_cipher.cipher import encrypt, decrypt
from chaos_cipher.fixed_point import from_float, to_float
from chaos_cipher.key_sensitivity import run_key_sensitivity
from chaos_cipher.metrics import npcr, uaci


IMAGE_SIZES = [(128, 128), (64, 64), (32, 32)]
INITIAL_CONDITIONS = [1.0, 2.0, 5.0]
Y0 = 1.0
Z0 = 1.0
WARMUP = 100


def make_image(width, height, pattern):
    """Generate deterministic test images with different spatial patterns."""
    data = bytearray()

    for y in range(height):
        for x in range(width):
            if pattern == "gradient":
                value = (3 * x + 5 * y) & 0xFF
            elif pattern == "checkerboard":
                value = 255 if ((x // 8 + y // 8) % 2) else 0
            else:
                value = (x * 17 + y * 29 + x * y) & 0xFF
            data.append(value)

    return bytes(data)


def evaluate_trial(plaintext, x0, width, height, pattern):
    """Measure sensitivity for one image and one initial condition."""
    base_q = from_float(x0)
    changed_q = base_q ^ 1

    base_x0 = to_float(base_q)
    changed_x0 = to_float(changed_q)

    cipher_a = encrypt(
        plaintext, x0=base_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )
    cipher_b = encrypt(
        plaintext, x0=changed_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )

    recovered_a = decrypt(
        cipher_a, x0=base_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )
    recovered_b = decrypt(
        cipher_b, x0=changed_x0, y0=Y0, z0=Z0, warmup=WARMUP
    )

    return {
        "image_pattern": pattern,
        "width": width,
        "height": height,
        "plaintext_bytes": len(plaintext),
        "base_x0_q16_16": base_q,
        "perturbed_x0_q16_16": changed_q,
        "key_lsb_difference": abs(base_q - changed_q),
        "warmup_iterations": WARMUP,
        "changed_ciphertext_bytes": sum(
            a != b for a, b in zip(cipher_a, cipher_b)
        ),
        "npcr_percent": npcr(cipher_a, cipher_b),
        "uaci_percent": uaci(cipher_a, cipher_b),
        "baseline_exact_recovery": recovered_a == plaintext,
        "perturbed_key_exact_recovery": recovered_b == plaintext,
    }


def summarize(rows, metric):
    values = [row[metric] for row in rows]
    return {
        "mean": statistics.mean(values),
        "sample_standard_deviation": (
            statistics.stdev(values) if len(values) > 1 else 0.0
        ),
        "minimum": min(values),
        "maximum": max(values),
    }


def main():
    rows = []

    patterns = ["gradient", "checkerboard", "mixed"]

    for width, height in IMAGE_SIZES:
        for pattern in patterns:
            plaintext = make_image(width, height, pattern)

            for x0 in INITIAL_CONDITIONS:
                rows.append(
                    evaluate_trial(plaintext, x0, width, height, pattern)
                )

    report = {
        "experiment": "Repeated Q16.16 one-LSB x0 key sensitivity",
        "cipher": "Existing Lorenz-keystream XOR baseline",
        "trial_count": len(rows),
        "warmup_iterations": WARMUP,
        "key_perturbation": "Flip bit 0 of the Q16.16 x0 representation",
        "npcr_percent": summarize(rows, "npcr_percent"),
        "uaci_percent": summarize(rows, "uaci_percent"),
        "all_baseline_recoveries_exact": all(
            row["baseline_exact_recovery"] for row in rows
        ),
        "all_perturbed_key_recoveries_exact": all(
            row["perturbed_key_exact_recovery"] for row in rows
        ),
        "trials": rows,
        "caveat": (
            "Descriptive results for this deterministic test set; "
            "not proof of cryptographic security."
        ),
    }

    output_dir = Path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "key_sensitivity_batch.json"
    csv_path = output_dir / "key_sensitivity_batch.csv"

    json_path.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("=== REPEATED KEY-SENSITIVITY TRIALS ===")
    print(f"Trials: {len(rows)}")
    print(
        f"NPCR mean ± sample SD: "
        f"{report['npcr_percent']['mean']:.6f}% ± "
        f"{report['npcr_percent']['sample_standard_deviation']:.6f}"
    )
    print(
        f"UACI mean ± sample SD: "
        f"{report['uaci_percent']['mean']:.6f}% ± "
        f"{report['uaci_percent']['sample_standard_deviation']:.6f}"
    )
    print(
        "All baseline recoveries exact:",
        report["all_baseline_recoveries_exact"],
    )
    print(
        "All perturbed-key recoveries exact:",
        report["all_perturbed_key_recoveries_exact"],
    )
    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")

    if not (
        report["all_baseline_recoveries_exact"]
        and report["all_perturbed_key_recoveries_exact"]
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
