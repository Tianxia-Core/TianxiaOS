// ffp: FFP-CPP-001 bitnet-ternary-simd cpp
// TianxiaOS Core 03 (Nimbus-SIMD) - Pratyangira Ingress Gate
// BitNet b1.58 Ternary Matrix Kernel & Vectorized Huber Probe

#ifndef BITNET_SIMD_KERNEL_HPP
#define BITNET_SIMD_KERNEL_HPP

#include <cstdint>
#include <cstddef>
#include <vector>

extern "C" {
    // Ternary dot product: weights in {-1, 0, 1}, activations in float
    float tx_bitnet_ternary_dot(const int8_t* weights, const float* activations, size_t length);

    // Vectorized Huber loss over residual stream
    float tx_vectorized_huber_loss(const float* activations, const float* safe_centroid, size_t length, float delta);
}

#endif // BITNET_SIMD_KERNEL_HPP
