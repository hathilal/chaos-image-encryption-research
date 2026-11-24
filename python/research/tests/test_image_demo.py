
import tempfile
import unittest
from pathlib import Path

from chaos_cipher.image_demo import (
    WIDTH,
    HEIGHT,
    PIXEL_COUNT,
    make_demo_image,
    write_pgm,
    run_demo,
)


class TestImageDemo(unittest.TestCase):
    def test_image_dimensions(self):
        pixels = make_demo_image()
        self.assertEqual(len(pixels), WIDTH * HEIGHT)
        self.assertEqual(len(pixels), PIXEL_COUNT)

    def test_pgm_file_header_and_pixel_data(self):
        pixels = make_demo_image()

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.pgm"
            write_pgm(path, pixels)
            content = path.read_bytes()

            header = f"P5\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
            self.assertTrue(content.startswith(header))
            self.assertEqual(content[len(header):], pixels)

    def test_complete_image_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(run_demo(tmp))

            plain = (Path(tmp) / "plain.pgm").read_bytes()
            decrypted = (Path(tmp) / "decrypted.pgm").read_bytes()
            self.assertEqual(plain, decrypted)

    def test_reject_wrong_pixel_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_pgm(Path(tmp) / "bad.pgm", b"\x00" * 10)


if __name__ == "__main__":
    unittest.main()
