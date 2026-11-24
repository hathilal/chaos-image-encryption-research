#include "lorenz_fixed.hpp"

#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>

int main() {
    constexpr std::uint64_t ITERATIONS = 1000000;

    chaos::State state = {
        chaos::from_double(1.0),
        chaos::from_double(1.0),
        chaos::from_double(1.0)
    };

    const auto start = std::chrono::steady_clock::now();

    for (std::uint64_t i = 0; i < ITERATIONS; ++i) {
        state = chaos::rk2_step(state);
    }

    const auto stop = std::chrono::steady_clock::now();

    const double seconds =
        std::chrono::duration<double>(stop - start).count();

    std::cout << "Kernel: fixed-point Lorenz RK2\n";
    std::cout << "Iterations: " << ITERATIONS << "\n";
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "Elapsed seconds: " << seconds << "\n";
    std::cout << std::setprecision(2);
    std::cout << "Steps per second: "
              << static_cast<double>(ITERATIONS) / seconds << "\n";
    std::cout << "Final state (Q16.16 integers): "
              << state.x << ", " << state.y << ", " << state.z << "\n";

    return 0;
}