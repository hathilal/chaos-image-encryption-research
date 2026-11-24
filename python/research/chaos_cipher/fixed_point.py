
"""Fixed-point arithmetic helpers: signed 32-bit Q16.16."""

WORD_BITS = 32
FRAC_BITS = 16
SCALE = 1 << FRAC_BITS
MASK = (1 << WORD_BITS) - 1
SIGN_BIT = 1 << (WORD_BITS - 1)


def wrap_signed(value: int) -> int:
    """Wrap an integer to signed 32-bit two's-complement."""
    value &= MASK
    if value & SIGN_BIT:
        value -= 1 << WORD_BITS
    return value


def from_float(value: float) -> int:
    """Convert a float to Q16.16."""
    return wrap_signed(round(value * SCALE))


def to_float(value: int) -> float:
    """Convert Q16.16 to a float."""
    return wrap_signed(value) / SCALE


def q_add(a: int, b: int) -> int:
    """Add with 32-bit wraparound."""
    return wrap_signed(a + b)


def q_sub(a: int, b: int) -> int:
    """Subtract with 32-bit wraparound."""
    return wrap_signed(a - b)


def q_mul(a: int, b: int) -> int:
    """Multiply Q16.16 values, then shift right by 16."""
    product = wrap_signed(a) * wrap_signed(b)
    return wrap_signed(product >> FRAC_BITS)


def q_div2(a: int) -> int:
    """Divide by two using an arithmetic right shift."""
    return wrap_signed(a) >> 1
