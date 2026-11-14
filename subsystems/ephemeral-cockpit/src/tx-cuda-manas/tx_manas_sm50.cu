#include <stdint.h>
#include <math.h>

#ifdef __CUDACC__
#include <cuda_runtime.h>

// Maxwell GM108 (CC 5.0, 384 Cores) Ephemeral Menu Node Scoring Kernel
__global__ void score_menu_nodes_sm50(
    const int8_t* __restrict__ node_embeddings, // [N_NODES x 256]
    const int8_t* __restrict__ intent_vector,   // [256] from Port 3109 MANAS
    const float*  __restrict__ telemetry_prior, // [N_NODES] live anomaly weight (e.g. Lease-002 Warn)
    uint16_t*     __restrict__ out_scores_q16,  // [N_NODES] output ephemeral luminance score
    int n_nodes
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= n_nodes) return;

    int32_t dot = 0;
    int32_t norm_a = 0;
    int32_t norm_b = 0;
    const int8_t* node_vec = node_embeddings + (idx * 256);

    #pragma unroll 8
    for (int i = 0; i < 256; ++i) {
        int32_t a = (int32_t)node_vec[i];
        int32_t b = (int32_t)intent_vector[i];
        dot += a * b;
        norm_a += a * a;
        norm_b += b * b;
    }

    float denom = sqrtf((float)norm_a) * sqrtf((float)norm_b) + 1e-6f;
    float cosine = (float)dot / denom;

    // SOFTEM Spike-Weighted Huber Boost for active system/financial anomalies
    float prior = telemetry_prior[idx];
    float delta = fabsf(prior);
    float huber_boost = (delta <= 1.0f) ? (0.5f * delta * delta) : (delta - 0.5f);

    float combined = fminf(fmaxf((cosine * 0.72f) + (huber_boost * 0.28f), 0.0f), 1.0f);
    out_scores_q16[idx] = (uint16_t)(combined * 65535.0f);
}

extern "C" int launch_ephemeral_scoring(
    const int8_t* d_nodes,
    const int8_t* d_intent,
    const float* d_prior,
    uint16_t* d_out,
    int n_nodes,
    cudaStream_t stream
) {
    int threads = 128;
    int blocks = (n_nodes + threads - 1) / threads;
    score_menu_nodes_sm50<<<blocks, threads, 0, stream>>>(d_nodes, d_intent, d_prior, d_out, n_nodes);
    return (int)cudaGetLastError();
}
#endif
