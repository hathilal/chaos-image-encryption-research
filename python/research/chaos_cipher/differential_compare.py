"""Compare plaintext sensitivity for XOR and permutation-diffusion."""

import csv
import json
from pathlib import Path

from chaos_cipher.cipher import encrypt as xor_encrypt
from chaos_cipher.permutation_diffusion import encrypt as pd_encrypt
from chaos_cipher.metrics import npcr, uaci

WIDTH = 128
HEIGHT = 128
WARMUP = 100
X0 = 1.0
Y0 = 1.0
Z0 = 1.0
IV = 0


def make_test_image():
    return bytes(
        (x * 3 + y * 5) & 0xFF
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )


def main():
    plain_a = make_test_image()

    changed = bytearray(plain_a)
    index = (HEIGHT // 2) * WIDTH + (WIDTH // 2)
    changed[index] ^= 0x01
    plain_b = bytes(changed)

    if sum(a != b for a, b in zip(plain_a, plain_b)) != 1:
        raise AssertionError("Expected exactly one changed plaintext byte")

    settings = {"x0": X0, "y0": Y0, "z0": Z0, "warmup": WARMUP}

    results = []
    for name, encrypt_fn, extra in (
        ("xor_baseline", xor_encrypt, {}),
        ("permutation_diffusion", pd_encrypt, {"iv": IV}),
    ):
        cipher_a = encrypt_fn(plain_a, **settings, **extra)
        cipher_b = encrypt_fn(plain_b, **settings, **extra)

        changed_bytes = sum(a != b for a, b in zip(cipher_a, cipher_b))

        results.append({
            "cipher": name,
            "width": WIDTH,
            "height": HEIGHT,
            "plaintext_changed_bytes": 1,
            "plaintext_change": "XOR 0x01 at center pixel",
            "x0": X0,
            "warmup": WARMUP,
            "iv": IV if name == "permutation_diffusion" else None,
            "ciphertext_length": len(cipher_a),
            "changed_ciphertext_bytes": changed_bytes,
            "npcr_percent": npcr(cipher_a, cipher_b),
            "uaci_percent": uaci(cipher_a, cipher_b),
        })

    root = Path(__file__).resolve().parents[2]
    out = root / "reports"
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "differential_comparison.json"
    csv_path = out / "differential_comparison.csv"

    json_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print("=== PLAINTEXT DIFFERENTIAL COMPARISON ===")
    print(f"Image: {WIDTH} x {HEIGHT}")
    print("Input change: one center pixel, XOR 0x01")
    for r in results:
        print(f"\n{r['cipher']}")
        print(f"  Changed ciphertext bytes: {r['changed_ciphertext_bytes']} / {r['ciphertext_length']}")
        print(f"  NPCR: {r['npcr_percent']:.6f}%")
        print(f"  UACI: {r['uaci_percent']:.6f}%")

    print(f"\nJSON report: {json_path}")
    print(f"CSV report: {csv_path}")
    print("Note: differential metrics alone do not establish cryptographic security.")


if __name__ == "__main__":
    main()
