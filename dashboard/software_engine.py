"""Integration layer for the repository's original Python cipher algorithms."""

import hashlib
import time
import sys
from pathlib import Path

PROJECT_PYTHON = Path(__file__).resolve().parents[1] / "python" / "research"
sys.path.insert(0, str(PROJECT_PYTHON))

from chaos_cipher.cipher import encrypt as xor_encrypt, decrypt as xor_decrypt
from chaos_cipher.permutation_diffusion import (
    encrypt as forward_encrypt,
    decrypt as forward_decrypt,
)
from chaos_cipher.bidirectional_diffusion import (
    encrypt as bidirectional_encrypt,
    decrypt as bidirectional_decrypt,
)
from chaos_cipher.metrics import (
    histogram_summary,
    adjacent_correlations,
    npcr,
    uaci,
)


ALGORITHMS = {
    "XOR baseline": (xor_encrypt, xor_decrypt),
    "Forward permutation-diffusion": (forward_encrypt, forward_decrypt),
    "Bidirectional permutation-diffusion": (
        bidirectional_encrypt,
        bidirectional_decrypt,
    ),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def run_software(data, algorithm, parameters, log):
    """Encrypt, decrypt, verify, and analyze one grayscale image payload."""

    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    if len(data) != 128 * 128:
        raise ValueError("Software Lab currently requires 128x128 grayscale input")

    encrypt_function, decrypt_function = ALGORITHMS[algorithm]

    log("SOFTWARE EXPERIMENT STARTED")
    log(f"Algorithm: {algorithm}")
    log(f"Input bytes: {len(data)}")
    log(f"Input SHA-256: {sha256(data)}")

    params = dict(parameters)
    if algorithm == "XOR baseline":
        params.pop("iv", None)

    log("Starting Python encryption")
    start = time.perf_counter()
    ciphertext = encrypt_function(data, **params)
    encryption_seconds = time.perf_counter() - start
    log(f"Python encryption completed: {encryption_seconds:.6f} seconds")

    log("Starting Python decryption")
    start = time.perf_counter()
    recovered = decrypt_function(ciphertext, **params)
    decryption_seconds = time.perf_counter() - start
    log(f"Python decryption completed: {decryption_seconds:.6f} seconds")

    mismatches = sum(a != b for a, b in zip(data, recovered))
    exact = len(data) == len(recovered) and mismatches == 0
    log(f"Recovery verification: {len(data) - mismatches}/{len(data)} pixels match")
    log("EXACT RECOVERY: " + ("PASS" if exact else "FAIL"))

    changed = bytearray(data)
    changed[0] = (changed[0] + 1) & 0xFF
    changed_ciphertext = encrypt_function(bytes(changed), **params)

    differential = {
        "npcr_percent": npcr(ciphertext, changed_ciphertext),
        "uaci_percent": uaci(ciphertext, changed_ciphertext),
    }

    summary = histogram_summary(ciphertext)
    correlations = adjacent_correlations(ciphertext, 128, 128)

    log("Differential test completed")
    log("Ciphertext analysis completed")
    log("SOFTWARE EXPERIMENT FINISHED")

    return {
        "ciphertext": ciphertext,
        "recovered": recovered,
        "exact_recovery": exact,
        "matching_pixels": len(data) - mismatches,
        "mismatched_pixels": mismatches,
        "input_sha256": sha256(data),
        "ciphertext_sha256": sha256(ciphertext),
        "recovered_sha256": sha256(recovered),
        "encryption_seconds": encryption_seconds,
        "decryption_seconds": decryption_seconds,
        "total_cipher_seconds": encryption_seconds + decryption_seconds,
        "entropy_bits_per_pixel": summary["standard_deviation"] * 0
            + _entropy(ciphertext),
        "histogram": summary["histogram"],
        "distinct_values": summary["distinct_values"],
        "mean": summary["mean"],
        "standard_deviation": summary["standard_deviation"],
        "neighbor_correlations": correlations,
        "differential_metrics": differential,
    }


def _entropy(data):
    import math
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    total = len(data)
    return -sum(
        (count / total) * math.log2(count / total)
        for count in counts if count
    )
