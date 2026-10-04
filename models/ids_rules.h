/*
 * Lightweight IoT Intrusion Detection System (IDS)
 * Hardware Deployment Header (Auto-Generated)
 * 
 * Model: Decision Tree (K=10)
 * Memory Footprint: ~4 KB
 * Dependencies: None (Bare-Metal C99)
 */

#ifndef IDS_RULES_H
#define IDS_RULES_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Feature Input Mapping (Array of 10 floats):
 *   features[0] : Weight
 *   features[1] : ack_count
 *   features[2] : Rate
 *   features[3] : IAT
 *   features[4] : syn_count
 *   features[5] : AVG
 *   features[6] : HTTPS
 *   features[7] : Tot size
 *   features[8] : ack_flag_number
 *   features[9] : syn_flag_number
 *
 * Returns:
 *   0 = Benign (Normal Safe Traffic)
 *   1 = Attack (Malicious Threat Detected)
 */
int predict_ids(const float* features);

#ifdef __cplusplus
}
#endif

#endif /* IDS_RULES_H */
