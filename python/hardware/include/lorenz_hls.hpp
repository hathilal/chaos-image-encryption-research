#ifndef LORENZ_HLS_HPP
#define LORENZ_HLS_HPP

#include <cstdint>

namespace chaos_hls {

using q16_t = std::int32_t;

struct State {
    q16_t x;
    q16_t y;
    q16_t z;
};

constexpr int FRAC_BITS = 16;
constexpr std::int64_t SCALE = std::int64_t{1} << FRAC_BITS;

constexpr q16_t SIGMA = 655360;
constexpr q16_t RHO = 1835008;
constexpr q16_t BETA = 174763;
constexpr q16_t H = 655;
constexpr q16_t HALF_H = 327;

// Convert to signed 32-bit two's-complement using explicit wraparound.
inline q16_t wrap_signed(std::int64_t value) {
    const std::uint32_t bits =
        static_cast<std::uint32_t>(static_cast<std::uint64_t>(value));

    if (bits <= 0x7FFFFFFFU) {
        return static_cast<q16_t>(bits);
    }

    return static_cast<q16_t>(
        static_cast<std::int64_t>(bits) - (std::int64_t{1} << 32)
    );
}

inline q16_t q_add(q16_t a, q16_t b) {
    return wrap_signed(static_cast<std::int64_t>(a) + b);
}

inline q16_t q_sub(q16_t a, q16_t b) {
    return wrap_signed(static_cast<std::int64_t>(a) - b);
}

// Reproduce Python's arithmetic right shift: floor(product / 2^16).
inline q16_t q_mul(q16_t a, q16_t b) {
    const std::int64_t product =
        static_cast<std::int64_t>(a) * static_cast<std::int64_t>(b);

    std::int64_t shifted = product / SCALE;
    if (product < 0 && (product % SCALE) != 0) {
        --shifted;
    }

    return wrap_signed(shifted);
}

inline q16_t q_div2(q16_t a) {
    std::int64_t value = a;
    if (value < 0 && (value % 2) != 0) {
        return static_cast<q16_t>((value / 2) - 1);
    }
    return static_cast<q16_t>(value / 2);
}

inline State lorenz_rhs(const State& s) {
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

// One fixed-point RK2 midpoint step.
// Keep operation order consistent with the Python reference.
inline State rk2_step(const State& s) {
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

}  // namespace chaos_hls

#endif