import csv
import json
import random
import statistics
from pathlib import Path

from chaos_cipher.cipher import encrypt as xor_encrypt
from chaos_cipher.cipher import decrypt as xor_decrypt
from chaos_cipher.permutation_diffusion import encrypt as pd_encrypt
from chaos_cipher.permutation_diffusion import decrypt as pd_decrypt
from chaos_cipher.metrics import npcr, uaci

WIDTH = 128
HEIGHT = 128
SIZE = WIDTH * HEIGHT
WARMUP = 100
SEED = 20261028

REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

# Deterministic synthetic grayscale image.
plaintext = bytes(
    ((x * 3 + y * 5) & 0xFF)
    for y in range(HEIGHT)
    for x in range(WIDTH)
)

# Five fixed positions plus 20 unique seeded random positions.
locations = [
    ("top_left", 0),
    ("top_right", WIDTH - 1),
    ("bottom_left", (HEIGHT - 1) * WIDTH),
    ("bottom_right", SIZE - 1),
    ("center", (HEIGHT // 2) * WIDTH + WIDTH // 2),
]

rng = random.Random(SEED)
used = {index for _, index in locations}

while len(locations) < 25:
    index = rng.randrange(SIZE)
    if index not in used:
        used.add(index)
        locations.append((f"random_{len(locations) - 4:02d}", index))

def encrypt_xor(data):
    return xor_encrypt(
        data, x0=1.0, y0=1.0, z0=1.0, warmup=WARMUP
    )

def decrypt_xor(data):
    return xor_decrypt(
        data, x0=1.0, y0=1.0, z0=1.0, warmup=WARMUP
    )

def encrypt_pd(data):
    return pd_encrypt(
        data, x0=1.0, y0=1.0, z0=1.0,
        warmup=WARMUP, iv=0
    )

def decrypt_pd(data):
    return pd_decrypt(
        data, x0=1.0, y0=1.0, z0=1.0,
        warmup=WARMUP, iv=0
    )

ciphers = {
    "xor_baseline": (encrypt_xor, decrypt_xor),
    "permutation_diffusion": (encrypt_pd, decrypt_pd),
}

baseline_ciphertexts = {
    name: encrypt(plaintext)
    for name, (encrypt, _) in ciphers.items()
}

rows = []

for label, index in locations:
    modified = bytearray(plaintext)
    modified[index] ^= 0x01
    modified = bytes(modified)

    for name, (encrypt, decrypt) in ciphers.items():
        original_ciphertext = baseline_ciphertexts[name]
        changed_ciphertext = encrypt(modified)

        changed_bytes = sum(
            a != b
            for a, b in zip(original_ciphertext, changed_ciphertext)
        )

        recovered_original = decrypt(original_ciphertext)
        recovered_modified = decrypt(changed_ciphertext)

        rows.append({
            "cipher": name,
            "position": label,
            "byte_index": index,
            "changed_ciphertext_bytes": changed_bytes,
            "npcr_percent": npcr(
                original_ciphertext, changed_ciphertext
            ),
            "uaci_percent": uaci(
                original_ciphertext, changed_ciphertext
            ),
            "exact_recovery": (
                recovered_original == plaintext
                and recovered_modified == modified
            ),
        })

summary = []

for name in ciphers:
    subset = [row for row in rows if row["cipher"] == name]
    record = {"cipher": name, "positions_tested": len(subset)}

    for metric in (
        "changed_ciphertext_bytes",
        "npcr_percent",
        "uaci_percent",
    ):
        values = [row[metric] for row in subset]
        record[f"mean_{metric}"] = statistics.mean(values)
        record[f"sd_{metric}"] = statistics.stdev(values)

    record["all_exact_recovery"] = all(
        row["exact_recovery"] for row in subset
    )
    summary.append(record)

report = {
    "experiment": "Batch single-bit plaintext differential sensitivity",
    "parameters": {
        "width": WIDTH,
        "height": HEIGHT,
        "plaintext_bytes": SIZE,
        "key_x0": 1.0,
        "key_y0": 1.0,
        "key_z0": 1.0,
        "warmup": WARMUP,
        "permutation_diffusion_iv": 0,
        "random_seed": SEED,
        "positions_tested": len(locations),
        "change": "Flip the least significant bit of one plaintext byte",
    },
    "summary": summary,
    "per_position": rows,
}

json_path = REPORTS / "differential_batch.json"
csv_path = REPORTS / "differential_batch.csv"

json_path.write_text(json.dumps(report, indent=2))

with csv_path.open("w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Positions tested per cipher: {len(locations)}")
print(f"Total measurements: {len(rows)}")
print()

for record in summary:
    print(f"Cipher: {record['cipher']}")
    print(
        "  Changed bytes: "
        f"{record['mean_changed_ciphertext_bytes']:.2f} "
        f"+/- {record['sd_changed_ciphertext_bytes']:.2f}"
    )
    print(
        f"  NPCR: {record['mean_npcr_percent']:.4f}% "
        f"+/- {record['sd_npcr_percent']:.4f} percentage points"
    )
    print(
        f"  UACI: {record['mean_uaci_percent']:.6f}% "
        f"+/- {record['sd_uaci_percent']:.6f} percentage points"
    )
    print(f"  Exact recovery for every case: {record['all_exact_recovery']}")
    print()

print(f"JSON report: {json_path}")
print(f"CSV report:  {csv_path}")
