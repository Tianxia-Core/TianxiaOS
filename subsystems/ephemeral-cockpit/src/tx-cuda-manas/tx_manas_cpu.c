// ffp: FFP-MANAS-AVX2 compute-kernel c
#include <stdint.h>
#include <math.h>
#include <immintrin.h>

// Intel i7-8850H AVX2 Ephemeral Menu Node Scorer
// Executes when GeForce MX130 is sleeping in RTD3 0.0W state
void score_menu_nodes_avx2(
    const int8_t* node_embeddings,
    const int8_t* intent_vector,
    const float*  telemetry_prior,
    uint16_t*     out_scores_q16,
    int n_nodes
) {
    for (int idx = 0; idx < n_nodes; ++idx) {
        const int8_t* node_vec = node_embeddings + (idx * 256);
        int32_t dot = 0;
        int32_t norm_a = 0;
        int32_t norm_b = 0;

        for (int i = 0; i < 256; ++i) {
            int32_t a = (int32_t)node_vec[i];
            int32_t b = (int32_t)intent_vector[i];
            dot += a * b;
            norm_a += a * a;
            norm_b += b * b;
        }

        float denom = sqrtf((float)norm_a) * sqrtf((float)norm_b) + 1e-6f;
        float cosine = (float)dot / denom;

        // SOFTEM Spike-Weighted Huber Boost
        float prior = telemetry_prior[idx];
        float delta = fabsf(prior);
        float huber_boost = (delta <= 1.0f) ? (0.5f * delta * delta) : (delta - 0.5f);

        float combined = fminf(fmaxf((cosine * 0.72f) + (huber_boost * 0.28f), 0.0f), 1.0f);
        out_scores_q16[idx] = (uint16_t)(combined * 65535.0f);
    }
}
