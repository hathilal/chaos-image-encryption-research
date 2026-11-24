
"""Statistical image-encryption evaluation metrics.

Uses only the Python standard library. NPCR and UACI compare two
ciphertext images of equal size, typically produced from plaintexts
that differ by one pixel while using the same key.
"""

from math import sqrt
from pathlib import Path


def validate_pixels(pixels):
    """Convert pixel data to bytes and reject empty inputs."""
    result = bytes(pixels)
    if not result:
        raise ValueError("Pixel data must not be empty")
    return result


def histogram(pixels):
    """Return a 256-bin histogram for 8-bit grayscale pixel data."""
    pixels = validate_pixels(pixels)
    counts = [0] * 256
    for value in pixels:
        counts[value] += 1
    return counts


def histogram_summary(pixels):
    """Return useful descriptive statistics for an image histogram."""
    pixels = validate_pixels(pixels)
    counts = histogram(pixels)
    total = len(pixels)
    mean = sum(pixels) / total
    variance = sum((value - mean) ** 2 for value in pixels) / total

    return {
        "pixel_count": total,
        "distinct_values": sum(count > 0 for count in counts),
        "mean": mean,
        "standard_deviation": sqrt(variance),
        "histogram": counts,
    }


def pearson_correlation(first, second):
    """Pearson correlation coefficient for paired numeric samples.

    Returns 0.0 when either input has zero variance. Such a result
    means the correlation is undefined, not that independence is proven.
    """
    if len(first) != len(second):
        raise ValueError("Inputs must have equal lengths")
    if len(first) < 2:
        raise ValueError("At least two samples are required")

    mean_a = sum(first) / len(first)
    mean_b = sum(second) / len(second)

    centered_a = [value - mean_a for value in first]
    centered_b = [value - mean_b for value in second]

    sum_a2 = sum(value * value for value in centered_a)
    sum_b2 = sum(value * value for value in centered_b)

    if sum_a2 == 0 or sum_b2 == 0:
        return 0.0

    cross = sum(
        a * b for a, b in zip(centered_a, centered_b)
    )
    return cross / sqrt(sum_a2 * sum_b2)


def adjacent_correlations(pixels, width, height):
    """Calculate horizontal, vertical, and diagonal pixel correlations."""
    pixels = validate_pixels(pixels)

    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")
    if len(pixels) != width * height:
        raise ValueError("Pixel count does not match width * height")

    horizontal_a, horizontal_b = [], []
    vertical_a, vertical_b = [], []
    diagonal_a, diagonal_b = [], []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            value = pixels[index]

            if x + 1 < width:
                horizontal_a.append(value)
                horizontal_b.append(pixels[index + 1])

            if y + 1 < height:
                vertical_a.append(value)
                vertical_b.append(pixels[index + width])

            if x + 1 < width and y + 1 < height:
                diagonal_a.append(value)
                diagonal_b.append(pixels[index + width + 1])

    def corr_or_none(a, b):
        if len(a) < 2:
            return None
        return pearson_correlation(a, b)

    return {
        "horizontal": corr_or_none(horizontal_a, horizontal_b),
        "vertical": corr_or_none(vertical_a, vertical_b),
        "diagonal": corr_or_none(diagonal_a, diagonal_b),
    }


def npcr(first, second):
    """Number of pixel change rate in percent between two images."""
    first = validate_pixels(first)
    second = validate_pixels(second)

    if len(first) != len(second):
        raise ValueError("Images must have equal pixel counts")

    changed = sum(a != b for a, b in zip(first, second))
    return 100.0 * changed / len(first)


def uaci(first, second):
    """Unified average changing intensity in percent."""
    first = validate_pixels(first)
    second = validate_pixels(second)

    if len(first) != len(second):
        raise ValueError("Images must have equal pixel counts")

    average_difference = sum(
        abs(a - b) for a, b in zip(first, second)
    ) / len(first)

    return 100.0 * average_difference / 255.0


def read_pgm(path):
    """Read a binary P5 8-bit grayscale PGM image.

    Supports the project's simple P5 header format. Comments and
    non-255 maximum pixel values are deliberately rejected.
    """
    data = Path(path).read_bytes()

    import re

    match = re.match(
        rb"P5\s+(\d+)\s+(\d+)\s+(\d+)\s",
        data,
    )
    if not match:
        raise ValueError(f"Unsupported PGM header: {path}")

    width, height, maximum = map(int, match.groups())
    if width <= 0 or height <= 0 or maximum != 255:
        raise ValueError("Expected positive dimensions and max value 255")

    pixels = data[match.end():]
    if len(pixels) != width * height:
        raise ValueError("PGM pixel data length does not match dimensions")

    return width, height, pixels


def print_image_report(name, pixels, width, height):
    """Print histogram and adjacent-pixel statistics."""
    stats = histogram_summary(pixels)
    correlations = adjacent_correlations(pixels, width, height)

    print(f"\n{name} ({width} x {height})")
    print(f"  Pixel count: {stats['pixel_count']}")
    print(f"  Distinct grayscale values: {stats['distinct_values']}/256")
    print(f"  Mean intensity: {stats['mean']:.4f}")
    print(f"  Standard deviation: {stats['standard_deviation']:.4f}")

    for direction, value in correlations.items():
        if value is None:
            print(f"  {direction.capitalize()} correlation: N/A")
        else:
            print(f"  {direction.capitalize()} correlation: {value:.6f}")


def main():
    image_dir = Path(__file__).resolve().parents[2] / "images" / "generated"
    names = ("plain", "cipher", "decrypted")
    images = {}

    for name in names:
        path = image_dir / f"{name}.pgm"
        if not path.exists():
            print(f"Missing {path}")
            print("Run the image demo first.")
            return 1

        width, height, pixels = read_pgm(path)
        images[name] = (width, height, pixels)

    for name in names:
        width, height, pixels = images[name]
        print_image_report(name, pixels, width, height)

    plain = images["plain"][2]
    decrypted = images["decrypted"][2]
    print("\nRound-trip verification")
    print(f"  Exact recovery: {plain == decrypted}")

    if plain == decrypted:
        print("  Plaintext and decrypted image bytes match exactly.")
    else:
        print("  WARNING: Decrypted image differs from the original.")

    print(
        "\nNPCR/UACI note: these require two ciphertexts made with the "
        "same key from two different plaintexts. Comparing plain vs "
        "cipher is not a valid differential-encryption test."
    )
    return 0 if plain == decrypted else 2


if __name__ == "__main__":
    raise SystemExit(main())
