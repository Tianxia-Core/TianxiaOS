/* ffp: FFP-MURUA-C-SRM compute-kernel c */
#include "tx_srm_acoustic_kernel.h"
#include <math.h>
#include <stdio.h>

void tx_srm_compute_acoustics(
    const SrmPlateConfig* config,
    const float* audio_samples,
    size_t sample_count,
    SrmAcousticResult* out_result
) {
    if (!config || !out_result) {
        return;
    }

    if (!audio_samples || sample_count < 16) {
        out_result->measured_f0_hz = config->f0_empty_hz;
        out_result->measured_zeta = config->zeta_empty;
        out_result->delta_f0_hz = 0.0;
        out_result->delta_inv_q = 0.0;
        out_result->estimated_mass_g = 0.0;
        out_result->is_loaded = 0;
        return;
    }

    // Zero-crossing and energy decay calculation for fundamental mode
    double total_energy = 0.0;
    size_t zero_crossings = 0;
    for (size_t i = 1; i < sample_count; ++i) {
        float s0 = audio_samples[i - 1];
        float s1 = audio_samples[i];
        total_energy += (double)(s1 * s1);
        if ((s0 >= 0.0f && s1 < 0.0f) || (s0 < 0.0f && s1 >= 0.0f)) {
            zero_crossings++;
        }
    }

    // Sampling rate assumption: 44100 Hz
    double sample_rate = 44100.0;
    double duration_sec = (double)sample_count / sample_rate;
    double estimated_freq = ((double)zero_crossings / (2.0 * duration_sec));

    // Clamp within plausible physical range [200 Hz, 800 Hz]
    if (estimated_freq < 200.0 || estimated_freq > 800.0) {
        estimated_freq = config->f0_empty_hz;
    }

    // Calculate energy decay envelope to estimate damping ratio zeta
    size_t half = sample_count / 2;
    double e_first = 1e-9;
    double e_second = 1e-9;
    for (size_t i = 0; i < half; ++i) {
        e_first += (double)(audio_samples[i] * audio_samples[i]);
    }
    for (size_t i = half; i < sample_count; ++i) {
        e_second += (double)(audio_samples[i] * audio_samples[i]);
    }

    double log_ratio = log(e_first / e_second);
    double estimated_zeta = config->zeta_empty;
    if (log_ratio > 0.0) {
        estimated_zeta = log_ratio / (2.0 * 3.141592653589793 * (double)zero_crossings / 2.0);
    }
    if (estimated_zeta < config->zeta_empty) {
        estimated_zeta = config->zeta_empty;
    }

    double delta_f0 = estimated_freq - config->f0_empty_hz;
    double delta_inv_q = 2.0 * (estimated_zeta - config->zeta_empty);

    // Invert mass loading equation: f_loaded = f_empty * (1 + delta_m'' / (rho_s * d))^(-0.5)
    double mass_g = 0.0;
    if (estimated_freq > 10.0 && estimated_freq < config->f0_empty_hz) {
        double ratio = config->f0_empty_hz / estimated_freq;
        double mass_ratio = ratio * ratio - 1.0;
        double plate_areal_mass = config->plate_density * config->plate_thickness_m;
        mass_g = mass_ratio * plate_areal_mass * config->tray_area_m2 * 1000.0;
    }

    out_result->measured_f0_hz = estimated_freq;
    out_result->measured_zeta = estimated_zeta;
    out_result->delta_f0_hz = delta_f0;
    out_result->delta_inv_q = delta_inv_q;
    out_result->estimated_mass_g = mass_g > 0.0 ? mass_g : 0.0;
    out_result->is_loaded = (delta_f0 <= -5.0 && delta_inv_q >= 0.010) ? 1 : 0;
}

int main(int argc, char** argv) {
    (void)argc;
    (void)argv;
    SrmPlateConfig cfg = {
        .f0_empty_hz = 420.0,
        .zeta_empty = 0.004,
        .plate_thickness_m = 0.0012,
        .plate_density = 7850.0,
        .tray_area_m2 = 0.0875
    };

    float dummy_waveform[1024];
    for (int i = 0; i < 1024; ++i) {
        // 405 Hz wave with decay representing loaded state (~65g envelope)
        double t = (double)i / 44100.0;
        dummy_waveform[i] = (float)(sin(2.0 * 3.1415926535 * 405.0 * t) * exp(-15.0 * t));
    }

    SrmAcousticResult res;
    tx_srm_compute_acoustics(&cfg, dummy_waveform, 1024, &res);

    printf("=== Murua SIMD C Acoustic Kernel Test ===\n");
    printf("Measured F0:     %.2f Hz\n", res.measured_f0_hz);
    printf("Measured Zeta:   %.5f\n", res.measured_zeta);
    printf("Delta F0:        %.2f Hz\n", res.delta_f0_hz);
    printf("Delta Q^-1:      %.5f\n", res.delta_inv_q);
    printf("Estimated Mass:  %.1f g\n", res.estimated_mass_g);
    printf("Is Loaded State: %s\n", res.is_loaded ? "TRUE (MAIL PRESENT)" : "FALSE (EMPTY)");
    return 0;
}
