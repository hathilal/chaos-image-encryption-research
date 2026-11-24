#include "lorenz_fixed.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>

namespace chaos {
namespace {

constexpr int FRAC_BITS = 16;
constexpr std::int64_t SCALE = std::int64_t{1} << FRAC_BITS;

constexpr q16_t SIGMA = 10 * static_cast<q16_t>(SCALE);
constexpr q16_t RHO = 28 * static_cast<q16_t>(SCALE);

// Match Python's from_float(8.0 / 3.0), which uses ties-to-even rounding.
constexpr q16_t BETA = 174763;
constexpr q16_t H = 655;
constexpr q16_t HALF_H = 327;

}  // namespace

q16_t wrap_signed(std::int64_t value) {
    const std::uint32_t bits = static_cast<std::uint32_t>(
        static_cast<std::uint64_t>(value)
    );

    if (bits <= 0x7FFFFFFFU) {
        return static_cast<q16_t>(bits);
    }

    const std::int64_t signed_value =
        static_cast<std::int64_t>(bits) - (std::int64_t{1} << 32);

    return static_cast<q16_t>(signed_value);
}

q16_t from_double(double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument("Q16.16 input must be finite");
    }

    const double scaled = value * static_cast<double>(SCALE);

    if (scaled < static_cast<double>(std::numeric_limits<std::int32_t>::min()) ||
        scaled > static_cast<double>(std::numeric_limits<std::int32_t>::max())) {
        throw std::out_of_range("Q16.16 input is outside signed 32-bit range");
    }

    // std::nearbyint uses the default round-to-nearest, ties-to-even mode.
    return wrap_signed(static_cast<std::int64_t>(std::nearbyint(scaled)));
}

double to_double(q16_t value) {
    return static_cast<double>(value) / static_cast<double>(SCALE);
}

q16_t q_add(q16_t a, q16_t b) {
    return wrap_signed(static_cast<std::int64_t>(a) + b);
}

q16_t q_sub(q16_t a, q16_t b) {
    return wrap_signed(static_cast<std::int64_t>(a) - b);
}

q16_t q_mul(q16_t a, q16_t b) {
    const std::int64_t product =
        static_cast<std::int64_t>(a) * static_cast<std::int64_t>(b);

    // Signed right shift is implementation-defined in older C++ standards.
    // This division explicitly reproduces floor(product / 2^16), including
    // negative products, as Python's arithmetic right shift does.
    std::int64_t shifted = product / SCALE;
    if (product < 0 && (product % SCALE) != 0) {
        --shifted;
    }

    return wrap_signed(shifted);
}

q16_t q_div2(q16_t a) {
    // Python's wrap_signed(a) >> 1 is an arithmetic shift.
    // Use explicit floor division for negative odd values.
    std::int64_t value = a;
    if (value < 0 && (value % 2) != 0) {
        return static_cast<q16_t>((value / 2) - 1);
    }
    return static_cast<q16_t>(value / 2);
}

State lorenz_rhs(const State& s) {
    const q16_t dx = q_mul(SIGMA, q_sub(s.y, s.x));

    const q16_t dy = q_sub(
        q_mul(s.x, q_sub(RHO, s.z)),
        s.y
    );

    const q16_t dz = q_sub(
        q_mul(s.x, s.y),
        q_mul(BETA, s.z)
    );

    return {dx, dy, dz};
}

State rk2_step(const State& s) {
    const State k1 = lorenz_rhs(s);

    const State midpoint = {
        q_add(s.x, q_mul(HALF_H, k1.x)),
        q_add(s.y, q_mul(HALF_H, k1.y)),
        q_add(s.z, q_mul(HALF_H, k1.z))
    };

    const State k2 = lorenz_rhs(midpoint);

    return {
        q_add(s.x, q_mul(H, k2.x)),
        q_add(s.y, q_mul(H, k2.y)),
        q_add(s.z, q_mul(H, k2.z))
    };
}

}  // namespace chaos