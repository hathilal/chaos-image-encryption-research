import json
from pathlib import Path

from chaos_cipher.bidirectional_diffusion import encrypt, decrypt
from chaos_cipher.metrics import npcr, uaci

SIZE = 128
plaintext = bytes(
    (x * 3 + y * 5) & 255
    for y in range(SIZE)
    for x in range(SIZE)
)

base_key = dict(x0=1.0, y0=1.0, z0=1.0, warmup=100, iv=0)

variants = {
    "baseline": {},
    "x0_plus_1e-6": {"x0": 1.000001},
    "y0_plus_1e-6": {"y0": 1.000001},
    "z0_plus_1e-6": {"z0": 1.000001},
}

def make_key(changes):
    return {**base_key, **changes}

results = []
ciphertexts = {}

for name, changes in variants.items():
    key = make_key(changes)
    ciphertext = encrypt(plaintext, **key)
    recovered = decrypt(ciphertext, **key)

    ciphertexts[name] = ciphertext

    results.append({
        "key_variant": name,
        "exact_recovery": recovered == plaintext,
    })

reference = ciphertexts["baseline"]

for result in results:
    name = result["key_variant"]

    if name == "baseline":
        continue

    changed = ciphertexts[name]

    result["npcr_percent"] = npcr(reference, changed)
    result["uaci_percent"] = uaci(reference, changed)
    result["changed_ciphertext_bytes"] = sum(
        a != b for a, b in zip(reference, changed)
    )

    wrong_key_recovery = decrypt(
        reference, **make_key(variants[name])
    )
    result["wrong_key_recovers_plaintext"] = (
        wrong_key_recovery == plaintext
    )

    print(f"\n{name}")
    print(f"  NPCR: {result['npcr_percent']:.4f}%")
    print(f"  UACI: {result['uaci_percent']:.4f}%")
    print(f"  Changed bytes: {result['changed_ciphertext_bytes']}")
    print(
        "  Wrong key recovers plaintext:",
        result["wrong_key_recovers_plaintext"],
    )

print("\nCorrect-key recovery:")
for result in results:
    print(f"  {result['key_variant']}: {result['exact_recovery']}")

Path("reports").mkdir(exist_ok=True)
Path("reports/key_sensitivity.json").write_text(
    json.dumps(results, indent=2)
)
print("\nSaved reports/key_sensitivity.json")
