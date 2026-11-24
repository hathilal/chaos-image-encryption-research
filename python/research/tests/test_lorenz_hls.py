import random
import subprocess
import tempfile
import unittest
from pathlib import Path

from chaos_cipher.lorenz import rk2_step


ROOT = Path(__file__).resolve().parents[2]
HEADER_DIR = ROOT / "hardware" / "include"
TESTBENCH = ROOT / "hardware" / "tests" / "test_lorenz_hls.cpp"


class TestLorenzHLSKernel(unittest.TestCase):
    def test_kernel_matches_python_reference(self):
        rng = random.Random(20261022)

        states = [
            (65536, 65536, 65536),
            (131072, 131072, 131072),
            (65536, 131072, 196608),
            (-65536, 65536, -131072),
            (2147480000, -2147480000, 65536),
            (-2147483648, 2147483647, -1),
            (2147483647, -2147483648, 1),
        ]

        # Full-width deterministic random inputs exercise overflow paths.
        for _ in range(200):
            states.append(tuple(
                rng.randint(-2147483648, 2147483647)
                for _ in range(3)
            ))

        input_text = "".join(
            f"{x} {y} {z}\n" for x, y, z in states
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "test_lorenz_hls"

            subprocess.run(
                [
                    "/usr/bin/g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    f"-I{HEADER_DIR}",
                    str(TESTBENCH),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            process = subprocess.run(
                [str(executable)],
                input=input_text,
                check=True,
                capture_output=True,
                text=True,
            )

        actual = [
            tuple(map(int, line.split(",")))
            for line in process.stdout.splitlines()
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