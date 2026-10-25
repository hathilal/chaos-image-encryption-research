"""Run a small Lorenz/RK2 demo and print selected states."""

from pathlib import Path
import sys

# Permit running the script from a source checkout without installing the package.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chaos_image_encryption import LorenzState, simulate_lorenz  # noqa: E402


def main() -> None:
    initial = LorenzState(x=1.0, y=1.0, z=1.0)
    states = simulate_lorenz(initial_state=initial, steps=1000, step_size=0.01)

    print("Floating-point Lorenz model using midpoint RK2")
    print(f"Initial state: {states[0]}")
    print(f"Number of steps: {len(states) - 1}")
    print(f"Final state:   {states[-1]}")
    print("\nFirst five states:")
    for index, state in enumerate(states[:5]):
        print(f"{index:4d}: x={state.x: .8f}, y={state.y: .8f}, z={state.z: .8f}")


if __name__ == "__main__":
    main()
