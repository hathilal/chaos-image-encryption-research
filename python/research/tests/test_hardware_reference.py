import random
import subprocess
import tempfile
import unittest
from pathlib import Path

from chaos_cipher.lorenz import rk2_step


ROOT = Path(__file__).resolve().parents[2]
CPP_SOURCE = ROOT / "hardware" / "src" / "lorenz_fixed.cpp"
CPP_TEST = ROOT / "hardware" / "tests" / "test_lorenz_fixed.cpp"
CPP_INCLUDE = ROOT / "hardware" / "include"


class TestHardwareReference(unittest.TestCase):
    def test_cpp_matches_python_for_105_states(self):
        rng = random.Random(20261021)

        states = [
            (65536, 65536, 65536),
            (131072, 131072, 131072),
            (65536, 131072, 196608),
            (-65536, 65536, -131072),
            (2147480000, -2147480000, 65536),
        ]

        for _ in range(100):
            states.append(tuple(
                rng.randint(-2_000_000, 2_000_000)
                for _ in range(3)
            ))

        input_text = "".join(
            f"{x} {y} {z}\n" for x, y, z in states
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "test_lorenz_fixed"

            subprocess.run(
                [
                    "/usr/bin/g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    f"-I{CPP_INCLUDE}",
                    str(CPP_SOURCE),
                    str(CPP_TEST),
                    "-o",
                    str(executable),
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [str(executable)],
                input=input_text,
                check=True,
                capture_output=True,
                text=True,
            )

        actual = [
            tuple(map(int, line.split(",")))
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        expected = [
            (i, *rk2_step(*state))
            for i, state in enumerate(states)
        ]

        self.assertEqual(len(actual), len(states))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()