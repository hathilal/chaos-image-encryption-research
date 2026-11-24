"""Multi-image, multi-key evaluation of the two cipher prototypes."""

import csv
import json
import statistics
import time
from pathlib import Path

from chaos_cipher.cipher import encrypt as xor_encrypt
from chaos_cipher.cipher import decrypt as xor_decrypt
from chaos_cipher.permutation_diffusion import encrypt as pd_encrypt
from chaos_cipher.permutation_diffusion import decrypt as pd_decrypt
from chaos_cipher.metrics import npcr, uaci

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def make_image(pattern, width=128, height=128):
    values = []
    for y in range(height):
        for x in range(width):
            if pattern == "gradient":
                value = (3 * x + 5 * y) & 255
            elif pattern == "checkerboard":
                value = 255 if ((x // 8 + y // 8) % 2) else 0
            elif pattern == "mixed":
                value = (x * 7 + y * 11 + x * y) & 255
            else:
                raise ValueError(f"Unknown pattern: {pattern}")
            values.append(value)
    return bytes(values)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    ciphers = {
        "xor_baseline": (xor_encrypt, xor_decrypt),
        "permutation_diffusion": (pd_encrypt, pd_decrypt),
    }

    rows = []
    for pattern in ("gradient", "checkerboard", "mixed"):
        plaintext = make_image(pattern)

        for x0 in (1.0, 2.0, 5.0):
            perturbed_x0 = x0 + 1.0 / 65536.0

            for name, (encrypt_fn, decrypt_fn) in ciphers.items():
                kwargs = {
                    "x0": x0, "y0": 1.0, "z0": 1.0, "warmup": 100
                }

                start = time.perf_counter()
                ciphertext = encrypt_fn(plaintext, **kwargs)
                encryption_seconds = time.perf_counter() - start

                start = time.perf_counter()
                recovered = decrypt_fn(ciphertext, **kwargs)
                decryption_seconds = time.perf_counter() - start

                perturbed_ciphertext = encrypt_fn(
                    plaintext,
                    x0=perturbed_x0,
                    y0=1.0,
                    z0=1.0,
                    warmup=100,
                )

                rows.append({
                    "cipher": name,
                    "pattern": pattern,
                    "x0": x0,
                    "warmup": 100,
                    "exact_recovery": recovered == plaintext,
                    "ciphertext_length": len(ciphertext),
                    "npcr_percent": round(
                        npcr(ciphertext, perturbed_ciphertext), 6
                    ),
                    "uaci_percent": round(
                        uaci(ciphertext, perturbed_ciphertext), 6
                    ),
                    "encryption_seconds": round(encryption_seconds, 6),
                    "decryption_seconds": round(decryption_seconds, 6),
                })

    csv_path = REPORTS / "cipher_evaluation.csv"
    json_path = REPORTS / "cipher_evaluation.json"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)

    print("MULTI-IMAGE / MULTI-KEY EVALUATION")
    print("=" * 72)

    for cipher_name in ciphers:
        subset = [row for row in rows if row["cipher"] == cipher_name]
        npcr_values = [row["npcr_percent"] for row in subset]
        uaci_values = [row["uaci_percent"] for row in subset]
        enc_values = [row["encryption_seconds"] for row in subset]

        print(f"\n{cipher_name}")
        print(f"  Trials: {len(subset)}")
        print(f"  Exact recovery: {sum(r['exact_recovery'] for r in subset)}"
              f"/{len(subset)}")
        print(f"  Mean NPCR: {statistics.mean(npcr_values):.4f}%")
        print(f"  NPCR sample SD: "
              f"{statistics.stdev(npcr_values):.4f} percentage points")
        print(f"  Mean UACI: {statistics.mean(uaci_values):.4f}%")
        print(f"  UACI sample SD: "
              f"{statistics.stdev(uaci_values):.4f} percentage points")
        print(f"  Mean encryption time: "
              f"{statistics.mean(enc_values):.6f} s")

    print(f"\nCSV report:  {csv_path}")
    print(f"JSON report: {json_path}")


if __name__ == "__main__":
    main()