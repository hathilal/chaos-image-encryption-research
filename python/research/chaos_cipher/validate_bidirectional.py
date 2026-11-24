import csv
import json
import random
import statistics
from pathlib import Path

from chaos_cipher.bidirectional_diffusion import encrypt, decrypt
from chaos_cipher.metrics import npcr, uaci

SEED = 20261028
PARAMS = dict(x0=1.0, y0=1.0, z0=1.0, warmup=100, iv=0)
SIZES = [64, 128]
PATTERNS = ["zeros", "gradient", "checkerboard", "random"]

def make_image(size, pattern, rng):
    data = bytearray()

    for y in range(size):
        for x in range(size):
            if pattern == "zeros":
                value = 0
            elif pattern == "gradient":
                value = (x * 3 + y * 5) & 255
            elif pattern == "checkerboard":
                value = 255 if ((x // 8 + y // 8) % 2) else 0
            else:
                value = rng.randrange(256)

            data.append(value)

    return bytes(data)

def test_positions(size, rng):
    last = size * size
    positions = {
        0,
        size - 1,
        (size - 1) * size,
        last - 1,
        (size // 2) * size + size // 2,
    }

    while len(positions) < 12:
        positions.add(rng.randrange(last))

    return sorted(positions)

rng = random.Random(SEED)
rows = []

for size in SIZES:
    for pattern in PATTERNS:
        plaintext = make_image(size, pattern, rng)
        reference = encrypt(plaintext, **PARAMS)

        assert decrypt(reference, **PARAMS) == plaintext

        positions = test_positions(size, rng)

        for index in positions:
            modified = bytearray(plaintext)
            modified[index] ^= 1
            modified = bytes(modified)

            changed = encrypt(modified, **PARAMS)

            rows.append({
                "size": size,
                "pattern": pattern,
                "byte_index": index,
                "npcr_percent": npcr(reference, changed),
                "uaci_percent": uaci(reference, changed),
                "changed_ciphertext_bytes": sum(
                    a != b for a, b in zip(reference, changed)
                ),
                "exact_recovery": (
                    decrypt(changed, **PARAMS) == modified
                ),
            })

groups = {}
for row in rows:
    key = (row["size"], row["pattern"])
    groups.setdefault(key, []).append(row)

summary = []
for (size, pattern), subset in groups.items():
    record = {
        "size": size,
        "pattern": pattern,
        "tests": len(subset),
        "mean_npcr_percent": statistics.mean(
            r["npcr_percent"] for r in subset
        ),
        "sd_npcr_percentage_points": statistics.stdev(
            r["npcr_percent"] for r in subset
        ),
        "mean_uaci_percent": statistics.mean(
            r["uaci_percent"] for r in subset
        ),
        "mean_changed_bytes": statistics.mean(
            r["changed_ciphertext_bytes"] for r in subset
        ),
        "all_exact_recovery": all(
            r["exact_recovery"] for r in subset
        ),
    }
    summary.append(record)

reports = Path("reports")
reports.mkdir(exist_ok=True)

(reports / "bidirectional_validation.json").write_text(
    json.dumps({
        "parameters": PARAMS,
        "seed": SEED,
        "positions_per_image": 12,
        "summary": summary,
        "per_position": rows,
    }, indent=2)
)

with (reports / "bidirectional_validation.csv").open(
    "w", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Total differential tests: {len(rows)}")
print()

for r in summary:
    print(f"{r['size']}x{r['size']} | {r['pattern']}")
    print(
        f"  NPCR: {r['mean_npcr_percent']:.4f}% "
        f"+/- {r['sd_npcr_percentage_points']:.4f} pp"
    )
    print(f"  UACI: {r['mean_uaci_percent']:.4f}%")
    print(f"  Mean changed bytes: {r['mean_changed_bytes']:.2f}")
    print(f"  Exact recovery: {r['all_exact_recovery']}")

print("\nSaved reports/bidirectional_validation.json")
print("Saved reports/bidirectional_validation.csv")
