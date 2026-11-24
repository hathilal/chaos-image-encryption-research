#include "lorenz_hls.hpp"

#include <iostream>

int main() {
    std::int64_t x, y, z;
    unsigned index = 0;

    while (std::cin >> x >> y >> z) {
        // Reject values outside signed 32-bit input range.
        if (x < -2147483648LL || x > 2147483647LL ||
            y < -2147483648LL || y > 2147483647LL ||
            z < -2147483648LL || z > 2147483647LL) {
            std::cerr << "Input outside signed 32-bit range\n";
            return 2;
        }

        const chaos_hls::State state = {
            static_cast<chaos_hls::q16_t>(x),
            static_cast<chaos_hls::q16_t>(y),
            static_cast<chaos_hls::q16_t>(z)
        };

        const chaos_hls::State result = chaos_hls::rk2_step(state);

        std::cout << index++ << ","
                  << result.x << ","
                  << result.y << ","
                  << result.z << "\n";
    }

    return 0;
}