#include "lorenz_fixed.hpp"

#include <cstdint>
#include <iostream>

int main() {
    std::int64_t x, y, z;
    unsigned index = 0;

    while (std::cin >> x >> y >> z) {
        const chaos::State state = {
            static_cast<chaos::q16_t>(x),
            static_cast<chaos::q16_t>(y),
            static_cast<chaos::q16_t>(z)
        };

        const chaos::State out = chaos::rk2_step(state);

        std::cout << index++ << ","
                  << out.x << ","
                  << out.y << ","
                  << out.z << "\n";
    }

    return 0;
}