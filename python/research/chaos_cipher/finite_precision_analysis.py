import csv
import json
from pathlib import Path

from chaos_cipher.fixed_point import from_float, wrap_signed
from chaos_cipher.lorenz import rk2_step


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports"

WARMUP = 100
MAX_STEPS = 100_000
STREAM_LENGTH = 16_384


def initial_state():
    return (
        from_float(1.0),
        from_float(1.0),
        from_float(1.0),
    )


def baseline_transition(state):
    next_state = rk2_step(*state)
    output_byte = (wrap_signed(next_state[0]) >> 8) & 0xFF
    return next_state, output_byte


def feedback_transition(state):
    next_state, output_byte = baseline_transition(state)
    x, y, z = next_state

    # Experimental one-LSB perturbation driven by the prior output byte.
    x = wrap_signed(x ^ (output_byte & 1))
    y = wrap_signed(y ^ ((output_byte >> 1) & 1))
    z = wrap_signed(z ^ ((output_byte >> 2) & 1))

    return (x, y, z), output_byte


def advance(state, transition, count):
    for _ in range(count):
        state, _ = transition(state)
    return state


def analyze(name, transition):
    state = advance(initial_state(), transition, WARMUP)

    # State -> step index allows exact detection of a repeated full state.
    seen = {}
    output = bytearray()
    cycle_length = None
    cycle_start = None

    for step in range(MAX_STEPS):
        if state in seen:
            cycle_start = seen[state]
            cycle_length = step - cycle_start
            break

        seen[state] = step
        state, value = transition(state)

        if len(output) < STREAM_LENGTH:
            output.append(value)

    bit_count = sum(byte.bit_count() for byte in output)
    total_bits = len(output) * 8

    return {
        "method": name,
        "warmup_steps": WARMUP,
        "max_cycle_search_steps": MAX_STEPS,
        "cycle_detected": cycle_length is not None,
        "cycle_start_step": cycle_start,
        "cycle_length_steps": cycle_length,
        "states_checked": len(seen),
        "output_bytes_analyzed": len(output),
        "unique_output_byte_values": len(set(output)),
        "one_bit_fraction": (
            bit_count / total_bits if total_bits else None
        ),
        "adjacent_equal_byte_fraction": (
            sum(a == b for a, b in zip(output, output[1:]))
            / (len(output) - 1)
            if len(output) > 1
            else None
        ),
    }


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = [
        analyze("baseline_q16_16", baseline_transition),
        analyze("one_lsb_state_feedback", feedback_transition),
    ]

    json_path = REPORT_DIR / "finite_precision_analysis.json"
    csv_path = REPORT_DIR / "finite_precision_analysis.csv"

    json_path.write_text(
        json.dumps(results, indent=2) + "\n",
        encoding="utf-8",
    )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys()),
        )
        writer.writeheader()
        writer.writerows(results)

    for result in results:
        print(f"\nMethod: {result['method']}")
        print(f"  States checked: {result['states_checked']}")
        print(f"  Cycle detected: {result['cycle_detected']}")
        print(f"  Cycle length: {result['cycle_length_steps']}")
        print(
            "  Unique byte values:",
            result["unique_output_byte_values"],
        )
        print(
            "  Output bit-one fraction:",
            result["one_bit_fraction"],
        )

    print(f"\nJSON report: {json_path.relative_to(ROOT)}")
    print(f"CSV report:  {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()