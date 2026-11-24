import csv
import hashlib
import json
import sys
from pathlib import Path

from chaos_cipher.permutation_diffusion import encrypt, decrypt


ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = ROOT / "images" / "validation"
REPORT_DIR = ROOT / "reports"
WIDTH = 128
HEIGHT = 128
PIXELS = WIDTH * HEIGHT


def make_images():
    gradient = bytes(
        (x * 2 + y) & 0xFF
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )

    checkerboard = bytes(
        255 if ((x // 8) + (y // 8)) % 2 else 0
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )

    stripes = bytes(
        255 if (x // 4) % 2 else 0
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )

    radial = bytes(
        int(min(255, (((x - 64) ** 2 + (y - 64) ** 2) ** 0.5) * 4))
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )

    mixed = bytes(
        (x * 17 + y * 31 + (x * y) % 251) & 0xFF
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )

    return {
        "gradient": gradient,
        "checkerboard": checkerboard,
        "stripes": stripes,
        "radial": radial,
        "mixed": mixed,
    }


def write_pgm(path, pixels):
    if len(pixels) != PIXELS:
        raise ValueError(f"Expected {PIXELS} pixels, got {len(pixels)}")

    path.write_bytes(
        f"P5\n{WIDTH} {HEIGHT}\n255\n".encode("ascii") + pixels
    )


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for name, plaintext in make_images().items():
        ciphertext = encrypt(
            plaintext,
            x0=1.0,
            y0=1.0,
            z0=1.0,
            warmup=100,
            iv=0,
        )

        recovered = decrypt(
            ciphertext,
            x0=1.0,
            y0=1.0,
            z0=1.0,
            warmup=100,
            iv=0,
        )

        exact_match = recovered == plaintext

        write_pgm(IMAGE_DIR / f"{name}_plain.pgm", plaintext)
        write_pgm(IMAGE_DIR / f"{name}_cipher.pgm", ciphertext)
        write_pgm(IMAGE_DIR / f"{name}_decrypted.pgm", recovered)

        result = {
            "image": name,
            "width": WIDTH,
            "height": HEIGHT,
            "pixel_bytes": len(plaintext),
            "exact_recovery": exact_match,
            "plaintext_sha256": sha256(plaintext),
            "recovered_sha256": sha256(recovered),
        }
        results.append(result)

        print(
            f"{name:12s} exact_recovery={exact_match} "
            f"pixels={len(plaintext)}"
        )

        if not exact_match:
            raise AssertionError(f"Exact recovery failed for {name}")

    json_path = REPORT_DIR / "five_image_validation.json"
    csv_path = REPORT_DIR / "five_image_validation.csv"

    json_path.write_text(
        json.dumps(results, indent=2) + "\n",
        encoding="utf-8",
    )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\nValidated {len(results)} images; all round trips passed.")
    print(f"JSON report: {json_path.relative_to(ROOT)}")
    print(f"CSV report:  {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()