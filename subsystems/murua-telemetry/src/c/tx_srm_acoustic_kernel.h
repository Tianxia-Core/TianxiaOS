/* ffp: FFP-MURUA-C-SRM compute-kernel c */
#ifndef TX_SRM_ACOUSTIC_KERNEL_H
#define TX_SRM_ACOUSTIC_KERNEL_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    double f0_empty_hz;
    double zeta_empty;
    double plate_thickness_m;
    double plate_density;
    double tray_area_m2;
} SrmPlateConfig;

typedef struct {
    double measured_f0_hz;
    double measured_zeta;
    double delta_f0_hz;
    double delta_inv_q;
    double estimated_mass_g;
    int is_loaded; // 1 if loaded, 0 if empty
} SrmAcousticResult;

/**
 * High-speed SIMD-friendly kernel calculating Lamb wave peak shift and damping.
 */
void tx_srm_compute_acoustics(
    const SrmPlateConfig* config,
    const float* audio_samples,
    size_t sample_count,
    SrmAcousticResult* out_result
);

#ifdef __cplusplus
}
#endif

#endif /* TX_SRM_ACOUSTIC_KERNEL_H */
