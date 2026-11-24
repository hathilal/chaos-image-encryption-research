"""Reproducible 1-LSB key-sensitivity warm-up experiment."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from chaos_cipher.fixed_point import from_float, to_float
from chaos_cipher.keystream import generate_keystream

WARMUP_VALUES = [0, 10, 50, 100, 250, 500, 1000]
INITIAL_CONDITIONS = [1.0, 2.0, 5.0]
OUTPUT_LENGTHS = [1024, 4096, 16384]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "reports"


def run_experiment():
    results = []

    for x0 in INITIAL_CONDITIONS:
        base_q = from_float(x0)
        changed_q = base_q ^ 1

        for warmup in WARMUP_VALUES:
            for length in OUTPUT_LENGTHS:
                first = generate_keystream(
                    length, x0=to_float(base_q),
                    y0=1.0, z0=1.0, warmup=warmup
                )
                second = generate_keystream(
                    length, x0=to_float(changed_q),
                    y0=1.0, z0=1.0, warmup=warmup
                )

                changed = sum(a != b for a, b in zip(first, second))
                npcr = 100.0 * changed / length

                results.append({
                    "base_x0": x0,
                    "base_x0_q16_16": base_q,
                    "changed_x0_q16_16": changed_q,
                    "key_difference_lsb": abs(changed_q - base_q),
                    "warmup_iterations": warmup,
                    "output_bytes": length,
                    "changed_bytes": changed,
                    "npcr_percent": round(npcr, 6),
                })

    return results


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results = run_experiment()
    csv_path = REPORT_DIR / "warmup_sensitivity.csv"
    json_path = REPORT_DIR / "warmup_sensitivity.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    report = {
        "experiment": "Direct keystream 1-LSB warm-up sensitivity",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_point_format": "Q16.16",
        "warmup_values": WARMUP_VALUES,
        "initial_conditions": INITIAL_CONDITIONS,
        "output_lengths_bytes": OUTPUT_LENGTHS,
        "trial_count": len(results),
        "note": (
            "NPCR measures differing keystream byte positions. "
            "High NPCR alone does not establish cryptographic security."
        ),
        "results": results,
    }

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("WARM-UP SENSITIVITY EXPERIMENT")
    print(f"Trials: {len(results)}")
    print(f"{'x0':>5} {'Warm-up':>8} {'Bytes':>7} {'NPCR (%)':>10}")

    for row in results:
        print(
            f"{row['base_x0']:5.1f} "
            f"{row['warmup_iterations']:8d} "
            f"{row['output_bytes']:7d} "
            f"{row['npcr_percent']:10.3f}"
        )

    print(f"\nCSV report:  {csv_path}")
    print(f"JSON report: {json_path}")


if __name__ == "__main__":
    main()