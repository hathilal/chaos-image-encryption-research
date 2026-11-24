#ifndef LORENZ_FIXED_HPP
#define LORENZ_FIXED_HPP

#include <cstdint>

namespace chaos {

using q16_t = std::int32_t;

struct State {
    q16_t x;
    q16_t y;
    q16_t z;
};

q16_t wrap_signed(std::int64_t value);
q16_t from_double(double value);
double to_double(q16_t value);

q16_t q_add(q16_t a, q16_t b);
q16_t q_sub(q16_t a, q16_t b);
q16_t q_mul(q16_t a, q16_t b);
q16_t q_div2(q16_t a);

State lorenz_rhs(const State& state);
State rk2_step(const State& state);

}  // namespace chaos

#endif