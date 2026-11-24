import csv
import json
import random
import statistics
from pathlib import Path

from chaos_cipher.permutation_diffusion import (
    encrypt as encrypt_forward,
    decrypt as decrypt_forward,
)
from chaos_cipher.bidirectional_diffusion import (
    encrypt as encrypt_bidir,
    decrypt as decrypt_bidir,
)
from chaos_cipher.metrics import npcr, uaci

WIDTH = HEIGHT = 128
SIZE = WIDTH * HEIGHT
WARMUP = 100
SEED = 20261028

plaintext = bytes(
    (x * 3 + y * 5) & 0xFF
    for y in range(HEIGHT)
    for x in range(WIDTH)
)

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

params = dict(x0=1.0, y0=1.0, z0=1.0, warmup=WARMUP, iv=0)
ciphers = {
    "forward_only": (encrypt_forward, decrypt_forward),
    "bidirectional": (encrypt_bidir, decrypt_bidir),
}

baseline = {
    name: enc(plaintext, **params)
    for name, (enc, _) in ciphers.items()
}
rows = []

for label, index in locations:
    modified = bytearray(plaintext)
    modified[index] ^= 1
    modified = bytes(modified)

    for name, (enc, dec) in ciphers.items():
        changed = enc(modified, **params)
        reference = baseline[name]
        count = sum(a != b for a, b in zip(reference, changed))

        rows.append({
            "cipher": name,
            "position": label,
            "byte_index": index,
            "changed_ciphertext_bytes": count,
            "npcr_percent": npcr(reference, changed),
            "uaci_percent": uaci(reference, changed),
            "exact_recovery": (
                dec(reference, **params) == plaintext
                and dec(changed, **params) == modified
            ),
        })

summary = []
for name in ciphers:
    subset = [r for r in rows if r["cipher"] == name]
    record = {"cipher": name, "positions_tested": len(subset)}
    for metric in ("changed_ciphertext_bytes", "npcr_percent", "uaci_percent"):
        values = [r[metric] for r in subset]
        record[f"mean_{metric}"] = statistics.mean(values)
        record[f"sd_{metric}"] = statistics.stdev(values)
    record["all_exact_recovery"] = all(r["exact_recovery"] for r in subset)
    summary.append(record)

reports = Path("reports")
reports.mkdir(exist_ok=True)
(reports / "diffusion_direction_comparison.json").write_text(
    json.dumps({"parameters": params, "summary": summary, "per_position": rows}, indent=2)
)
with (reports / "diffusion_direction_comparison.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

for r in summary:
    print(f"\n{r['cipher']} ({r['positions_tested']} positions)")
    print(f"  Mean changed bytes: {r['mean_changed_ciphertext_bytes']:.2f} +/- {r['sd_changed_ciphertext_bytes']:.2f}")
    print(f"  Mean NPCR: {r['mean_npcr_percent']:.4f}% +/- {r['sd_npcr_percent']:.4f} pp")
    print(f"  Mean UACI: {r['mean_uaci_percent']:.6f}% +/- {r['sd_uaci_percent']:.6f} pp")
    print(f"  Exact recovery all cases: {r['all_exact_recovery']}")

print("\nSaved reports/diffusion_direction_comparison.json")
print("Saved reports/diffusion_direction_comparison.csv")
