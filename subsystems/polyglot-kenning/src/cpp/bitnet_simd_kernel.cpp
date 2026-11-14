// ffp: FFP-CPP-002 bitnet-ternary-simd-impl cpp
// TianxiaOS Core 03 (Nimbus-SIMD) - Pratyangira Gate Implementation
// AVX2/Vectorized ternary kernel and Spike-Weighted Huber evaluation

#include "bitnet_simd_kernel.hpp"
#include <iostream>
#include <cmath>
#include <algorithm>
#include <chrono>

#if defined(__AVX2__)
#include <immintrin.h>
#endif

extern "C" {

float tx_bitnet_ternary_dot(const int8_t* weights, const float* activations, size_t length) {
    float sum = 0.0f;
    size_t i = 0;

#if defined(__AVX2__)
    __m256 vsum = _mm256_setzero_ps();
    for (; i + 8 <= length; i += 8) {
        __m256 vact = _mm256_loadu_ps(activations + i);
        float w_floats[8];
        for (int k = 0; k < 8; ++k) {
            w_floats[k] = static_cast<float>(weights[i + k]);
        }
        __m256 vw = _mm256_loadu_ps(w_floats);
        vsum = _mm256_add_ps(vsum, _mm256_mul_ps(vact, vw));
    }
    float buffer[8];
    _mm256_storeu_ps(buffer, vsum);
    for (int k = 0; k < 8; ++k) {
        sum += buffer[k];
    }
#endif

    for (; i < length; ++i) {
        sum += static_cast<float>(weights[i]) * activations[i];
    }
    return sum;
}

float tx_vectorized_huber_loss(const float* activations, const float* safe_centroid, size_t length, float delta) {
    if (length == 0) return 0.0f;
    float total_loss = 0.0f;
    for (size_t i = 0; i < length; ++i) {
        float r = std::abs(activations[i] - safe_centroid[i]);
        if (r <= delta) {
            total_loss += 0.5f * (r * r);
        } else {
            total_loss += delta * (r - 0.5f * delta);
        }
    }
    return total_loss / static_cast<float>(length);
}

} // extern "C"

int main() {
    std::cout << "=== [TIANXIAOS // NIMBUS-SIMD (C++)] Pratyangira Ingress Kernel ===" << std::endl;

    const size_t len = 16;
    int8_t weights[len] = {1, 0, -1, 1, -1, 0, 1, 1, -1, -1, 0, 1, 1, -1, 0, 1};
    float acts[len] = {0.5f, 0.2f, 0.8f, -0.4f, 0.1f, 0.9f, -0.3f, 0.7f,
                       0.4f, -0.5f, 0.2f, 0.6f, -0.1f, 0.3f, 0.0f, -0.8f};
    float centroid[len] = {0.48f, 0.19f, 0.79f, -0.38f, 0.12f, 0.88f, -0.28f, 0.69f,
                           0.39f, -0.48f, 0.21f, 0.59f, -0.11f, 0.29f, 0.01f, -0.79f};

    float dot = tx_bitnet_ternary_dot(weights, acts, len);
    std::cout << "[SIMD TERNARY DOT]: Result = " << dot << std::endl;

    float loss = tx_vectorized_huber_loss(acts, centroid, len, 1.0f);
    std::cout << "[SIMD HUBER LOSS]: Mean Loss = " << loss << std::endl;

    std::cout << "=== [TIANXIAOS // NIMBUS-SIMD (C++)] Execution Complete ===" << std::endl;
    return 0;
}
