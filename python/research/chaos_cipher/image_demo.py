
"""128x128 grayscale image encryption demo using PGM files."""

from pathlib import Path

from chaos_cipher.cipher import encrypt, decrypt

WIDTH = 128
HEIGHT = 128
PIXEL_COUNT = WIDTH * HEIGHT


def make_demo_image() -> bytes:
    """Generate a deterministic 128x128 grayscale test pattern."""
    pixels = bytearray()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            value = (2 * x + 3 * y) % 256
            pixels.append(value)

    return bytes(pixels)


def write_pgm(path: str | Path, pixels: bytes) -> None:
    """Write an 8-bit grayscale PGM image."""
    if len(pixels) != PIXEL_COUNT:
        raise ValueError(
            f"Expected {PIXEL_COUNT} pixels, received {len(pixels)}"
        )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as file:
        file.write(f"P5\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        file.write(pixels)


def run_demo(output_dir: str | Path = "images/generated") -> bool:
    """Save the plain, encrypted, and decrypted demo images."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    original = make_demo_image()
    ciphertext = encrypt(original)
    recovered = decrypt(ciphertext)

    write_pgm(output_dir / "plain.pgm", original)
    write_pgm(output_dir / "cipher.pgm", ciphertext)
    write_pgm(output_dir / "decrypted.pgm", recovered)

    if recovered != original:
        raise AssertionError("Image round-trip verification failed")

    print(f"Image dimensions: {WIDTH} x {HEIGHT}")
    print(f"Pixel bytes: {len(original)}")
    print(f"Encrypted bytes: {len(ciphertext)}")
    print(f"Exact round trip: {recovered == original}")
    print(f"Images saved to: {output_dir.resolve()}")

    return True


if __name__ == "__main__":
    run_demo()
